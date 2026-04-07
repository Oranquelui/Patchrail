from __future__ import annotations

import json
import time
from typing import Any

from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import CostMetrics, Plan, Task
from patchrail.models.roles import Provider, RoleCandidate
from patchrail.providers.http import post_json
from patchrail.runners.base import RunnerResult


def execute_api_candidate(candidate: RoleCandidate, task: Task, plan: Plan) -> RunnerResult:
    api_key = _require_env(candidate.api_key_env)
    started = time.perf_counter()
    payload: dict[str, Any]
    if candidate.provider == Provider.CODEX:
        payload = _call_openai(candidate, api_key, task, plan)
        raw_text = _extract_openai_text(payload)
    elif candidate.provider == Provider.CLAUDE:
        payload = _call_anthropic(candidate, api_key, task, plan)
        raw_text = _extract_anthropic_text(payload)
    elif candidate.provider == Provider.GROK:
        payload = _call_xai(candidate, api_key, task, plan)
        raw_text = _extract_xai_text(payload)
    else:
        raise PatchrailError(f"Unsupported API provider '{candidate.provider.value}'.")

    response = _parse_execution_json(raw_text)
    elapsed = time.perf_counter() - started
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    return RunnerResult(
        stdout=raw_text.strip() + "\n",
        stderr="",
        execution_summary=str(response["execution_summary"]).strip(),
        diff_summary=str(response["diff_summary"]).strip() + "\n",
        cost_metrics=CostMetrics(
            prompt_tokens=int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("output_tokens") or usage.get("completion_tokens") or 0),
            estimated_usd=0.0,
            elapsed_seconds=round(elapsed, 3),
        ),
        exit_code=0,
    )


def _call_openai(candidate: RoleCandidate, api_key: str, task: Task, plan: Plan) -> dict[str, Any]:
    base_url = _normalized_base_url(candidate.endpoint_env, "https://api.openai.com/v1")
    return post_json(
        url=f"{base_url}/responses",
        headers={"Authorization": f"Bearer {api_key}"},
        body={
            "model": candidate.model or "gpt-5.2-codex",
            "input": _execution_prompt(task, plan),
        },
    )


def _call_anthropic(candidate: RoleCandidate, api_key: str, task: Task, plan: Plan) -> dict[str, Any]:
    base_url = _normalized_base_url(candidate.endpoint_env, "https://api.anthropic.com")
    return post_json(
        url=f"{base_url}/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        body={
            "model": candidate.model or "claude-sonnet-4-20250514",
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": _execution_prompt(task, plan)}],
        },
    )


def _call_xai(candidate: RoleCandidate, api_key: str, task: Task, plan: Plan) -> dict[str, Any]:
    base_url = _normalized_base_url(candidate.endpoint_env, "https://api.x.ai/v1")
    return post_json(
        url=f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        body={
            "model": candidate.model or "grok-4-0709",
            "messages": [{"role": "user", "content": _execution_prompt(task, plan)}],
        },
    )


def _execution_prompt(task: Task, plan: Plan) -> str:
    steps = "\n".join(f"- {step}" for step in plan.steps)
    return (
        "You are an executor inside Patchrail, a supervised local-first coding-agent control plane. "
        "Do not claim files were edited. Return JSON only with keys execution_summary and diff_summary. "
        "execution_summary must be markdown text. diff_summary must be markdown bullet text. "
        "Summarize the intended execution for the task and plan below.\n\n"
        f"Task Title: {task.title}\n"
        f"Task Description: {task.description}\n"
        f"Plan Summary: {plan.summary}\n"
        f"Plan Steps:\n{steps}\n"
    )


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


def _parse_execution_json(raw_text: str) -> dict[str, str]:
    payload = _load_json(raw_text)
    if not isinstance(payload, dict):
        raise PatchrailError("Executor API response was not valid JSON.")
    execution_summary = payload.get("execution_summary")
    diff_summary = payload.get("diff_summary")
    if not isinstance(execution_summary, str) or not execution_summary.strip():
        raise PatchrailError("Executor API response missing execution_summary.")
    if not isinstance(diff_summary, str) or not diff_summary.strip():
        raise PatchrailError("Executor API response missing diff_summary.")
    return {"execution_summary": execution_summary, "diff_summary": diff_summary}


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


def _require_env(env_name: str | None) -> str:
    if not env_name:
        raise PatchrailError("API candidate is missing api_key_env.")
    import os

    value = os.getenv(env_name)
    if not value:
        raise PatchrailError(f"Required environment variable '{env_name}' is not set.")
    return value


def _normalized_base_url(env_name: str | None, default: str) -> str:
    import os

    if env_name:
        value = os.getenv(env_name)
        if value:
            return value.rstrip("/")
    return default.rstrip("/")
