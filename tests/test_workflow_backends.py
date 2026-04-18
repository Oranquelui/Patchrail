from __future__ import annotations

from pathlib import Path

import pytest

from patchrail.models.entities import ArtifactBundle, Plan, PlanStatus, ReviewVerdict, Run, RunStatus, Task, TaskState
from patchrail.models.entities import CostMetrics, RunnerAssignment
from patchrail.models.roles import AccessMode, CapabilityProfile, Provider, Role, RoleCandidate


def _simulation_candidate(*, role: Role, name: str, provider: Provider = Provider.CLAUDE) -> RoleCandidate:
    capabilities_by_role = {
        Role.PLANNER: CapabilityProfile(supports_planning=True, supports_json_output=True, supports_noninteractive=True),
        Role.REVIEWER: CapabilityProfile(supports_review=True, supports_json_output=True, supports_noninteractive=True),
    }
    return RoleCandidate(
        name=name,
        role=role,
        provider=provider,
        access_mode=AccessMode.SUBSCRIPTION,
        capability_profile=capabilities_by_role[role],
        simulation=True,
    )


def test_langgraph_planner_backend_returns_graph_metadata() -> None:
    pytest.importorskip("langgraph")
    from patchrail.workflows.langgraph_backend import LangGraphWorkflowEngine

    engine = LangGraphWorkflowEngine()
    result = engine.generate_plan(
        _simulation_candidate(role=Role.PLANNER, name="claude_subscription_planner"),
        Task(
            id="task_test",
            title="LangGraph planner",
            description="Exercise the planner graph",
            state=TaskState.CREATED,
            created_at="2026-04-18T00:00:00Z",
            updated_at="2026-04-18T00:00:00Z",
        ),
    )

    assert result.summary
    assert result.steps
    assert result.metadata["graph"] == "planner"
    assert result.metadata["graph_version"] == "mvp.v1"
    assert result.metadata["checkpointer"] == "stateless"
    assert result.metadata["delegate_backend"] == "local"
    assert result.metadata["candidate_name"] == "claude_subscription_planner"
    assert result.metadata["provider"] == "claude"
    assert result.metadata["node_trace"] == [
        "collect_plan_context",
        "generate_plan",
        "validate_plan",
        "finalize_plan",
    ]


def test_langgraph_reviewer_backend_returns_graph_metadata(tmp_path: Path) -> None:
    pytest.importorskip("langgraph")
    from patchrail.workflows.langgraph_backend import LangGraphWorkflowEngine

    engine = LangGraphWorkflowEngine()

    execution_summary = tmp_path / "execution-summary.md"
    execution_summary.write_text("# Summary\n")
    diff_summary = tmp_path / "diff-summary.md"
    diff_summary.write_text("- diff\n")

    result = engine.generate_review(
        _simulation_candidate(role=Role.REVIEWER, name="codex_subscription_reviewer", provider=Provider.CODEX),
        Task(
            id="task_test",
            title="LangGraph reviewer",
            description="Exercise the reviewer graph",
            state=TaskState.REVIEW_PENDING,
            created_at="2026-04-18T00:00:00Z",
            updated_at="2026-04-18T00:00:00Z",
        ),
        Plan(
            id="plan_test",
            task_id="task_test",
            summary="Plan summary",
            steps=["Inspect", "Review"],
            status=PlanStatus.READY,
            created_at="2026-04-18T00:00:00Z",
        ),
        Run(
            id="run_test",
            task_id="task_test",
            plan_id="plan_test",
            runner_assignment=RunnerAssignment(
                runner_name="claude_code",
                mode="shell",
                command="python -m patchrail.runners.local_harness",
                assigned_by="codex",
                assigned_at="2026-04-18T00:00:00Z",
            ),
            status=RunStatus.COMPLETED,
            created_at="2026-04-18T00:00:00Z",
            completed_at="2026-04-18T00:00:01Z",
            cost_metrics=CostMetrics(
                prompt_tokens=1,
                completion_tokens=1,
                estimated_usd=0.0,
                elapsed_seconds=0.1,
            ),
            artifact_bundle_id="run_test",
            workspace_path=str(tmp_path),
            exit_code=0,
            summary="Run summary",
        ),
        ArtifactBundle(
            run_id="run_test",
            created_at="2026-04-18T00:00:01Z",
            files={
                "execution_summary": str(execution_summary),
                "diff_summary": str(diff_summary),
            },
            summary="Bundle summary",
        ),
    )

    assert result.verdict == ReviewVerdict.PASS
    assert result.summary
    assert result.metadata["graph"] == "reviewer"
    assert result.metadata["graph_version"] == "mvp.v1"
    assert result.metadata["checkpointer"] == "stateless"
    assert result.metadata["delegate_backend"] == "local"
    assert result.metadata["candidate_name"] == "codex_subscription_reviewer"
    assert result.metadata["provider"] == "codex"
    assert result.metadata["run_id"] == "run_test"
    assert result.metadata["artifact_bundle_id"] == "run_test"
    assert result.metadata["node_trace"] == [
        "collect_review_context",
        "generate_review",
        "validate_review",
        "finalize_review",
    ]
