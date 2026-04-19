from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import ArtifactBundle, Plan, ReviewVerdict, Run, Task
from patchrail.models.roles import AccessMode, Provider, RoleCandidate
from patchrail.providers.http import post_json
from patchrail.workflows.base import PlanWorkflowResult, ReviewWorkflowResult, WorkflowEngine


class LocalWorkflowEngine(WorkflowEngine):
    backend_name = "local"

    def generate_plan(self, candidate: RoleCandidate, task: Task) -> PlanWorkflowResult:
        summary, steps = _generate_plan_content(candidate, task)
        return PlanWorkflowResult(
            summary=summary,
            steps=steps,
            metadata={"generation_mode": _generation_mode(candidate)},
        )

    def generate_review(
        self,
        candidate: RoleCandidate,
        task: Task,
        plan: Plan,
        run: Run,
        bundle: ArtifactBundle,
    ) -> ReviewWorkflowResult:
        verdict, summary = _generate_review_content(candidate, task, plan, run, bundle)
        return ReviewWorkflowResult(
            verdict=verdict,
            summary=summary,
            metadata={"generation_mode": _generation_mode(candidate)},
        )


def _generation_mode(candidate: RoleCandidate) -> str:
    return "simulation" if candidate.simulation else "live_provider"


def _generate_plan_content(candidate: RoleCandidate, task: Task) -> tuple[str, list[str]]:
    if candidate.simulation:
        return _simulated_plan(task)

    payload = _generate_payload(candidate, _planning_prompt(task), role_label="planner")
    summary = payload.get("summary")
    steps = payload.get("steps")
    if not isinstance(summary, str) or not summary.strip():
        raise PatchrailError("Planner response missing summary.")
    if not isinstance(steps, list) or not steps or not all(isinstance(step, str) and step.strip() for step in steps):
        raise PatchrailError("Planner response missing steps.")
    return summary.strip(), [step.strip() for step in steps]


def _generate_review_content(
    candidate: RoleCandidate,
    task: Task,
    plan: Plan,
    run: Run,
    bundle: ArtifactBundle,
) -> tuple[ReviewVerdict, str]:
    if candidate.simulation:
        return _simulated_review(run)

    payload = _generate_payload(
        candidate,
        _review_prompt(task, plan, run, bundle),
        role_label="reviewer",
        workspace_dir=Path(run.workspace_path),
    )
    verdict = payload.get("verdict")
    summary = payload.get("summary")
    if verdict not in {"pass", "fail"}:
        raise PatchrailError("Reviewer response missing verdict.")
    if not isinstance(summary, str) or not summary.strip():
        raise PatchrailError("Reviewer response missing summary.")
    return ReviewVerdict(verdict), summary.strip()


def _simulated_plan(task: Task) -> tuple[str, list[str]]:
    return (
        f"Auto-generated plan for {task.title}",
        [
            "Inspect the task scope and constraints.",
            "Prepare a bounded execution pass.",
            "Collect outputs for review and approval.",
        ],
    )


def _simulated_review(run: Run) -> tuple[ReviewVerdict, str]:
    if run.exit_code != 0:
        return ReviewVerdict.FAIL, "Automatic simulated review marked the run as failing because the exit code was non-zero."
    return ReviewVerdict.PASS, "Automatic simulated review found no blocking issues in the persisted run artifacts."


def _generate_payload(
    candidate: RoleCandidate,
    prompt: str,
    role_label: str,
    workspace_dir: Path | None = None,
) -> dict[str, Any]:
    raw_text = _generate_text(candidate, prompt, role_label=role_label, workspace_dir=workspace_dir)
    payload = _load_json(raw_text)
    if not isinstance(payload, dict):
        raise PatchrailError(f"{role_label.capitalize()} response was not valid JSON.")
    return payload


def _generate_text(
    candidate: RoleCandidate,
    prompt: str,
    role_label: str,
    workspace_dir: Path | None = None,
) -> str:
    if candidate.access_mode == AccessMode.API:
        return _complete_via_api(candidate, prompt)
    if candidate.access_mode == AccessMode.SUBSCRIPTION and candidate.provider == Provider.CLAUDE:
        return _complete_via_claude_subscription(candidate, prompt)
    if candidate.access_mode == AccessMode.SUBSCRIPTION and candidate.provider == Provider.CODEX:
        return _complete_via_codex_subscription(candidate, prompt, workspace_dir=workspace_dir)
    raise PatchrailError(
        f"Automatic {role_label} generation is not supported for candidate '{candidate.name}'. "
        "Use another access mode or adjust the role policy."
    )


def _planning_prompt(task: Task) -> str:
    return (
        "You are the planner inside Patchrail, a supervised local-first coding-agent control plane. "
        "Return JSON only with keys summary and steps. "
        "summary must be a single concise sentence. "
        "steps must be an array of 3 to 5 short imperative strings.\n\n"
        f"Task Title: {task.title}\n"
        f"Task Description: {task.description}\n"
    )


def _review_prompt(task: Task, plan: Plan, run: Run, bundle: ArtifactBundle) -> str:
    execution_summary = _read_bundle_file(bundle, "execution_summary", default=run.summary)
    diff_summary = _read_bundle_file(bundle, "diff_summary", default="")
    steps = "\n".join(f"- {step}" for step in plan.steps)
    return (
        "You are the reviewer inside Patchrail, a supervised local-first coding-agent control plane. "
        "Return JSON only with keys verdict and summary. "
        "verdict must be either pass or fail. "
        "summary must be a concise rationale grounded in the supplied run artifacts.\n\n"
        f"Task Title: {task.title}\n"
        f"Task Description: {task.description}\n"
        f"Plan Summary: {plan.summary}\n"
        f"Plan Steps:\n{steps}\n\n"
        f"Run Summary:\n{execution_summary}\n\n"
        f"Diff Summary:\n{diff_summary}\n"
    )


def _read_bundle_file(bundle: ArtifactBundle, key: str, default: str) -> str:
    path_value = bundle.files.get(key)
    if not path_value:
        return default
    path = Path(path_value)
    if not path.exists():
        return default
    return path.read_text().strip() or default


def _complete_via_api(candidate: RoleCandidate, prompt: str) -> str:
    api_key = _require_env(candidate.api_key_env)
    if candidate.provider == Provider.CODEX:
        payload = post_json(
            url=f"{_normalized_base_url(candidate.endpoint_env, 'https://api.openai.com/v1')}/responses",
            headers={"Authorization": f"Bearer {api_key}"},
            body={"model": candidate.model or "gpt-5.2-codex", "input": prompt},
        )
        return _extract_openai_text(payload)
    if candidate.provider == Provider.CLAUDE:
        payload = post_json(
            url=f"{_normalized_base_url(candidate.endpoint_env, 'https://api.anthropic.com')}/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            body={
                "model": candidate.model or "claude-sonnet-4-20250514",
                "max_tokens": 1200,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        return _extract_anthropic_text(payload)
    if candidate.provider == Provider.GROK:
        payload = post_json(
            url=f"{_normalized_base_url(candidate.endpoint_env, 'https://api.x.ai/v1')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            body={"model": candidate.model or "grok-4-0709", "messages": [{"role": "user", "content": prompt}]},
        )
        return _extract_xai_text(payload)
    raise PatchrailError(f"Unsupported API provider '{candidate.provider.value}'.")


def _complete_via_claude_subscription(candidate: RoleCandidate, prompt: str) -> str:
    command = [
        candidate.cli_command or "claude",
        "-p",
        "--output-format",
        "json",
        "--dangerously-skip-permissions",
        "--allowedTools",
        "",
    ]
    if candidate.model:
        command.extend(["--model", candidate.model])
    completed = subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise PatchrailError(f"Claude subscription generation failed: {detail}")
    payload = _load_json(completed.stdout)
    if not isinstance(payload, dict):
        raise PatchrailError("Claude subscription generation returned an invalid payload.")
    result = payload.get("result")
    if not isinstance(result, str) or not result.strip():
        raise PatchrailError("Claude subscription generation returned no result text.")
    return result.strip()


def _complete_via_codex_subscription(
    candidate: RoleCandidate,
    prompt: str,
    workspace_dir: Path | None,
) -> str:
    if workspace_dir is None:
        raise PatchrailError("Codex subscription generation requires a workspace directory.")
    workspace_dir.mkdir(parents=True, exist_ok=True)
    last_message_path = workspace_dir / "codex-review-last-message.txt"
    command = [
        candidate.cli_command or "codex",
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--json",
        "--output-last-message",
        str(last_message_path),
        "-",
    ]
    if candidate.model:
        command[2:2] = ["--model", candidate.model]
    completed = subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
        cwd=workspace_dir,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise PatchrailError(f"Codex subscription generation failed: {detail}")
    if not last_message_path.exists():
        raise PatchrailError("Codex subscription generation produced no final message.")
    result = last_message_path.read_text().strip()
    if not result:
        raise PatchrailError("Codex subscription generation produced an empty final message.")
    return result


def _extract_openai_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return str(payload["output_text"]).strip()
    output = payload.get("output")
    if not isinstance(output, list):
        raise PatchrailError("OpenAI response did not include output text.")
    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for chunk in content:
            if not isinstance(chunk, dict):
                continue
            text_value = chunk.get("text")
            if isinstance(text_value, str) and text_value.strip():
                parts.append(text_value.strip())
    if not parts:
        raise PatchrailError("OpenAI response did not include output text.")
    return "\n".join(parts).strip()


def _extract_anthropic_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        raise PatchrailError("Anthropic response did not include content blocks.")
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "text":
            continue
        text_value = item.get("text")
        if isinstance(text_value, str) and text_value.strip():
            parts.append(text_value.strip())
    if not parts:
        raise PatchrailError("Anthropic response did not include text output.")
    return "\n".join(parts).strip()


def _extract_xai_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise PatchrailError("xAI response did not include choices.")
    first = choices[0]
    if not isinstance(first, dict):
        raise PatchrailError("xAI response choice was not an object.")
    message = first.get("message")
    if not isinstance(message, dict):
        raise PatchrailError("xAI response did not include a message.")
    text_value = message.get("content")
    if not isinstance(text_value, str) or not text_value.strip():
        raise PatchrailError("xAI response did not include message content.")
    return text_value.strip()


def _load_json(raw_text: str) -> Any:
    raw = raw_text.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    if raw.startswith("```") and raw.endswith("```"):
        lines = raw.splitlines()
        inner = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(inner)
        except json.JSONDecodeError:
            return None
    for line in reversed(raw.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def _normalized_base_url(env_name: str | None, default: str) -> str:
    if not env_name:
        return default
    return _require_env(env_name).rstrip("/")


def _require_env(name: str | None) -> str:
    if not name:
        raise PatchrailError("Missing required provider configuration.")
    import os

    value = os.getenv(name)
    if value is None or not value.strip():
        raise PatchrailError(f"Required environment variable '{name}' is missing.")
    return value.strip()
