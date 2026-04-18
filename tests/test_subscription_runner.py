from __future__ import annotations

import subprocess
from pathlib import Path

from patchrail.models.entities import CostMetrics, Plan, PlanStatus, Task, TaskState
from patchrail.models.roles import AccessMode, CapabilityProfile, Provider, Role, RoleCandidate
from patchrail.runners.subscription import build_subscription_runner


def test_build_subscription_runner_supports_codex_provider() -> None:
    runner = build_subscription_runner(_subscription_candidate(provider=Provider.CODEX), runner_name="codex_runner")

    assert runner.mode == "subscription"
    assert runner.command == "provider-subscription:codex"


def test_codex_subscription_runner_executes_codex_exec_and_parses_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    candidate = _subscription_candidate(provider=Provider.CODEX)
    runner = build_subscription_runner(candidate, runner_name="codex_runner")
    task = Task(
        id="task_codex",
        title="Codex subscription execution",
        description="Execute through Codex CLI",
        state=TaskState.PLANNED,
        created_at="2026-04-18T00:00:00Z",
        updated_at="2026-04-18T00:00:00Z",
    )
    plan = Plan(
        id="plan_codex",
        task_id=task.id,
        summary="Execute the plan",
        steps=["Inspect workspace", "Return JSON only"],
        status=PlanStatus.READY,
        created_at="2026-04-18T00:00:00Z",
    )

    captured: dict[str, object] = {}

    def fake_run(command, input, capture_output, text, cwd, check):  # noqa: ANN001
        captured["command"] = command
        captured["input"] = input
        captured["cwd"] = cwd
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text('{"execution_summary":"# Codex summary","diff_summary":"- Codex diff"}\n')
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"type":"thread.started"}\n{"type":"turn.completed"}\n',
            stderr="",
        )

    monkeypatch.setattr("patchrail.runners.subscription.subprocess.run", fake_run)

    result = runner.run(task=task, plan=plan, workspace_path=tmp_path, run_id="run_codex")

    assert captured["command"][:2] == ["codex", "exec"]
    assert "--skip-git-repo-check" in captured["command"]
    assert "--json" in captured["command"]
    assert "--output-last-message" in captured["command"]
    assert "--sandbox" in captured["command"]
    assert captured["cwd"] == tmp_path
    assert "Task Title: Codex subscription execution" in str(captured["input"])
    assert result.stdout == '{"type":"thread.started"}\n{"type":"turn.completed"}\n'
    assert result.stderr == ""
    assert result.execution_summary == "# Codex summary"
    assert result.diff_summary == "- Codex diff\n"
    assert result.cost_metrics == CostMetrics(
        prompt_tokens=0,
        completion_tokens=0,
        estimated_usd=0.0,
        elapsed_seconds=result.cost_metrics.elapsed_seconds,
    )
    assert result.cost_metrics.elapsed_seconds >= 0.0


def _subscription_candidate(provider: Provider) -> RoleCandidate:
    return RoleCandidate(
        name=f"{provider.value}_subscription_executor",
        role=Role.EXECUTOR,
        provider=provider,
        access_mode=AccessMode.SUBSCRIPTION,
        capability_profile=CapabilityProfile(
            supports_execution=True,
            supports_json_output=True,
            supports_noninteractive=True,
        ),
        cli_command=provider.value,
    )
