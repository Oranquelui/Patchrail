from __future__ import annotations

import subprocess
from pathlib import Path

from patchrail.models.entities import ArtifactBundle, CostMetrics, Plan, PlanStatus, Run, RunStatus, RunnerAssignment, Task, TaskState
from patchrail.models.roles import AccessMode, CapabilityProfile, Provider, Role, RoleCandidate
from patchrail.workflows.local import LocalWorkflowEngine


def test_local_workflow_engine_supports_codex_subscription_reviewer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    engine = LocalWorkflowEngine()
    execution_summary = tmp_path / "execution-summary.md"
    execution_summary.write_text("# Summary\n")
    diff_summary = tmp_path / "diff-summary.md"
    diff_summary.write_text("- diff\n")

    task = Task(
        id="task_review",
        title="Codex reviewer",
        description="Review through Codex subscription",
        state=TaskState.REVIEW_PENDING,
        created_at="2026-04-19T00:00:00Z",
        updated_at="2026-04-19T00:00:00Z",
    )
    plan = Plan(
        id="plan_review",
        task_id=task.id,
        summary="Review the output",
        steps=["Inspect bundle", "Return verdict"],
        status=PlanStatus.READY,
        created_at="2026-04-19T00:00:00Z",
    )
    run = Run(
        id="run_review",
        task_id=task.id,
        plan_id=plan.id,
        runner_assignment=RunnerAssignment(
            runner_name="claude_code",
            mode="shell",
            command="python -m patchrail.runners.local_harness",
            assigned_by="codex",
            assigned_at="2026-04-19T00:00:00Z",
        ),
        status=RunStatus.COMPLETED,
        created_at="2026-04-19T00:00:00Z",
        completed_at="2026-04-19T00:00:01Z",
        cost_metrics=CostMetrics(
            prompt_tokens=1,
            completion_tokens=1,
            estimated_usd=0.0,
            elapsed_seconds=0.1,
        ),
        artifact_bundle_id="run_review",
        workspace_path=str(tmp_path),
        exit_code=0,
        summary="Run summary",
    )
    bundle = ArtifactBundle(
        run_id=run.id,
        created_at="2026-04-19T00:00:01Z",
        files={
            "execution_summary": str(execution_summary),
            "diff_summary": str(diff_summary),
        },
        summary="Bundle summary",
    )

    captured: dict[str, object] = {}

    def fake_run(command, input, capture_output, text, check, cwd):  # noqa: ANN001
        captured["command"] = command
        captured["input"] = input
        captured["cwd"] = cwd
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text('{"verdict":"pass","summary":"Codex reviewer summary"}\n')
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"type":"thread.started"}\n{"type":"turn.completed"}\n',
            stderr="",
        )

    monkeypatch.setattr("patchrail.workflows.local.subprocess.run", fake_run)

    result = engine.generate_review(
        _codex_subscription_reviewer(),
        task,
        plan,
        run,
        bundle,
    )

    assert captured["command"][:2] == ["codex", "exec"]
    assert "--skip-git-repo-check" in captured["command"]
    assert "--sandbox" in captured["command"]
    assert "read-only" in captured["command"]
    assert "--json" in captured["command"]
    assert "--output-last-message" in captured["command"]
    assert captured["cwd"] == tmp_path
    assert "Task Title: Codex reviewer" in str(captured["input"])
    assert result.verdict.value == "pass"
    assert result.summary == "Codex reviewer summary"
    assert result.metadata["generation_mode"] == "live_provider"


def _codex_subscription_reviewer() -> RoleCandidate:
    return RoleCandidate(
        name="codex_subscription_reviewer",
        role=Role.REVIEWER,
        provider=Provider.CODEX,
        access_mode=AccessMode.SUBSCRIPTION,
        capability_profile=CapabilityProfile(
            supports_review=True,
            supports_json_output=True,
            supports_noninteractive=True,
        ),
        cli_command="codex",
    )
