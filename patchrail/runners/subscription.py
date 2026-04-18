from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import CostMetrics, Plan, Task
from patchrail.models.roles import Provider, RoleCandidate
from patchrail.runners.base import Runner, RunnerResult


class ClaudeSubscriptionRunner(Runner):
    def __init__(self, candidate: RoleCandidate, runner_name: str) -> None:
        self._candidate = candidate
        self.name = runner_name
        self.mode = "subscription"
        self.command = "provider-subscription:claude"

    def run(self, task: Task, plan: Plan, workspace_path: Path, run_id: str) -> RunnerResult:
        command = [
            self._candidate.cli_command or "claude",
            "-p",
            "--output-format",
            "json",
            "--dangerously-skip-permissions",
            "--allowedTools",
            "",
        ]
        if self._candidate.model:
            command.extend(["--model", self._candidate.model])
        completed = subprocess.run(
            command,
            input=_execution_prompt(task, plan),
            capture_output=True,
            text=True,
            cwd=workspace_path,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise PatchrailError(f"Claude subscription runner failed: {detail}")

        payload = _parse_cli_payload(completed.stdout)
        result_text = payload.get("result")
        if not isinstance(result_text, str) or not result_text.strip():
            raise PatchrailError("Claude subscription runner returned no result text.")
        response = _parse_execution_json(result_text, provider_label="Claude subscription")
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        total_cost = payload.get("total_cost_usd")
        return RunnerResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            execution_summary=response["execution_summary"],
            diff_summary=response["diff_summary"] + "\n",
            cost_metrics=CostMetrics(
                prompt_tokens=int(usage.get("input_tokens") or 0),
                completion_tokens=int(usage.get("output_tokens") or 0),
                estimated_usd=float(total_cost or 0.0),
                elapsed_seconds=round(float(payload.get("duration_ms") or 0) / 1000.0, 3),
            ),
            exit_code=0,
        )


class CodexSubscriptionRunner(Runner):
    def __init__(self, candidate: RoleCandidate, runner_name: str) -> None:
        self._candidate = candidate
        self.name = runner_name
        self.mode = "subscription"
        self.command = "provider-subscription:codex"

    def run(self, task: Task, plan: Plan, workspace_path: Path, run_id: str) -> RunnerResult:
        last_message_path = workspace_path / "codex-last-message.txt"
        command = [
            self._candidate.cli_command or "codex",
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--json",
            "--output-last-message",
            str(last_message_path),
            "-",
        ]
        if self._candidate.model:
            command[2:2] = ["--model", self._candidate.model]
        started_at = time.monotonic()
        completed = subprocess.run(
            command,
            input=_execution_prompt(task, plan),
            capture_output=True,
            text=True,
            cwd=workspace_path,
            check=False,
        )
        elapsed_seconds = round(time.monotonic() - started_at, 3)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise PatchrailError(f"Codex subscription runner failed: {detail}")
        if not last_message_path.exists():
            raise PatchrailError("Codex subscription runner produced no final message.")
        result_text = last_message_path.read_text().strip()
        if not result_text:
            raise PatchrailError("Codex subscription runner produced an empty final message.")
        response = _parse_execution_json(result_text, provider_label="Codex subscription")
        return RunnerResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            execution_summary=response["execution_summary"],
            diff_summary=response["diff_summary"] + "\n",
            cost_metrics=CostMetrics(
                prompt_tokens=0,
                completion_tokens=0,
                estimated_usd=0.0,
                elapsed_seconds=elapsed_seconds,
            ),
            exit_code=0,
        )


def build_subscription_runner(candidate: RoleCandidate, runner_name: str) -> Runner:
    if candidate.provider == Provider.CLAUDE:
        return ClaudeSubscriptionRunner(candidate=candidate, runner_name=runner_name)
    if candidate.provider == Provider.CODEX:
        return CodexSubscriptionRunner(candidate=candidate, runner_name=runner_name)
    raise PatchrailError(f"Unsupported subscription runner provider '{candidate.provider.value}'.")


def _execution_prompt(task: Task, plan: Plan) -> str:
    steps = "\n".join(f"- {step}" for step in plan.steps)
    return (
        "You are an executor inside Patchrail, a supervised local-first coding-agent control plane. "
        "Return JSON only with keys execution_summary and diff_summary. "
        "execution_summary must be markdown text. diff_summary must be markdown bullet text. "
        "Do not claim files were edited.\n\n"
        f"Task Title: {task.title}\n"
        f"Task Description: {task.description}\n"
        f"Plan Summary: {plan.summary}\n"
        f"Plan Steps:\n{steps}\n"
    )


def _parse_cli_payload(raw: str) -> dict[str, object]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PatchrailError("Claude subscription runner returned non-JSON output.") from exc
    if not isinstance(payload, dict):
        raise PatchrailError("Claude subscription runner returned an invalid payload.")
    return payload


def _parse_execution_json(raw_text: str, provider_label: str) -> dict[str, str]:
    payload = _load_json(raw_text)
    if not isinstance(payload, dict):
        raise PatchrailError(f"{provider_label} result was not valid JSON.")
    execution_summary = payload.get("execution_summary")
    diff_summary = payload.get("diff_summary")
    if not isinstance(execution_summary, str) or not execution_summary.strip():
        raise PatchrailError(f"{provider_label} result missing execution_summary.")
    if not isinstance(diff_summary, str) or not diff_summary.strip():
        raise PatchrailError(f"{provider_label} result missing diff_summary.")
    return {"execution_summary": execution_summary.strip(), "diff_summary": diff_summary.strip()}


def _load_json(raw_text: str) -> object:
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
