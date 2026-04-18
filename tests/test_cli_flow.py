from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from patchrail.cli.main import main
from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import CostMetrics
from patchrail.models.entities import ReviewVerdict
from patchrail.runners.base import RunnerResult


def run_cli(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, object]]:
    exit_code = main(args)
    captured = capsys.readouterr()
    payload = json.loads(captured.out) if captured.out.strip() else {}
    return exit_code, payload


def test_happy_path_persists_state_artifacts_and_ledgers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code, config_payload = run_cli(["config", "init"], capsys)
    assert exit_code == 0
    assert Path(config_payload["config"]["path"]).exists()

    exit_code, created = run_cli(
        ["task", "create", "--title", "Bootstrap foundation", "--description", "Create Patchrail MVP"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]
    assert created["task"]["state"] == "created"

    exit_code, planned = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Implement MVP", "--step", "Scaffold", "--step", "Test"],
        capsys,
    )
    assert exit_code == 0
    plan_id = planned["plan"]["id"]
    assert planned["task"]["state"] == "planned"

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "claude_code"], capsys)
    assert exit_code == 0
    run_id = executed["run"]["id"]
    assert executed["run"]["status"] == "completed"
    assert executed["task"]["state"] == "review_pending"
    assert executed["artifact_bundle"]["run_id"] == run_id
    assert executed["run"]["runner_assignment"]["mode"] == "shell"
    workspace_path = Path(executed["run"]["workspace_path"])
    assert workspace_path.exists()
    assert (workspace_path / "task.json").exists()
    assert (workspace_path / "plan.json").exists()

    exit_code, reviewed = run_cli(
        ["review", "--run-id", run_id, "--verdict", "pass", "--summary", "Looks good"],
        capsys,
    )
    assert exit_code == 0
    review_id = reviewed["review"]["id"]
    assert reviewed["task"]["state"] == "awaiting_approval"

    exit_code, approved = run_cli(["approve", "--task-id", task_id, "--rationale", "Ship it"], capsys)
    assert exit_code == 0
    approval_id = approved["approval"]["id"]
    assert approved["task"]["state"] == "approved"

    exit_code, status_payload = run_cli(["status", "--task-id", task_id], capsys)
    assert exit_code == 0
    assert status_payload["task"]["id"] == task_id
    assert status_payload["plan"]["id"] == plan_id
    assert status_payload["latest_run"]["id"] == run_id
    assert status_payload["latest_review"]["id"] == review_id
    assert status_payload["latest_approval"]["id"] == approval_id

    exit_code, logs_payload = run_cli(["logs", "--run-id", run_id], capsys)
    assert exit_code == 0
    assert "local harness stdout" in logs_payload["stdout"]
    assert "claude_code" in logs_payload["stdout"]

    exit_code, artifacts_payload = run_cli(["artifacts", "--run-id", run_id], capsys)
    assert exit_code == 0
    bundle = artifacts_payload["artifact_bundle"]
    assert bundle["run_id"] == run_id
    artifact_paths = {name: Path(path) for name, path in bundle["files"].items()}
    for path in artifact_paths.values():
        assert path.exists()
    artifact_manifest = bundle["artifacts"]
    assert artifact_manifest["stdout"]["logical_kind"] == "runner_stdout"
    assert artifact_manifest["stderr"]["logical_kind"] == "runner_stderr"
    assert artifact_manifest["execution_summary"]["logical_kind"] == "execution_summary"
    assert artifact_manifest["diff_summary"]["logical_kind"] == "diff_summary"
    assert artifact_manifest["invocation"]["logical_kind"] == "runner_invocation"
    assert artifact_manifest["trace"]["logical_kind"] == "runner_trace"
    assert artifact_manifest["trace"]["collection_status"] == "collected"
    assert artifact_manifest["trace"]["media_type"] == "application/json"
    assert len(artifact_manifest["trace"]["sha256"]) == 64
    assert artifact_manifest["trace"]["size_bytes"] > 0
    assert "invocation" in artifact_paths
    invocation = json.loads(artifact_paths["invocation"].read_text())
    assert invocation["mode"] == "shell"
    assert "patchrail.runners.local_harness" in invocation["command"]
    assert invocation["workspace_path"] == str(workspace_path)
    trace = json.loads(artifact_paths["trace"].read_text())
    assert trace["schema_version"] == "patchrail.runner_trace.v1"
    assert trace["runner_name"] == "claude_code"
    assert trace["run_id"] == run_id

    storage_root = tmp_path / ".patchrail"
    assert (storage_root / "tasks" / f"{task_id}.json").exists()
    assert (storage_root / "plans" / f"{plan_id}.json").exists()
    assert (storage_root / "runs" / f"{run_id}.json").exists()
    assert (storage_root / "reviews" / f"{review_id}.json").exists()
    assert (storage_root / "approvals" / f"{approval_id}.json").exists()

    trace_entries = (storage_root / "ledgers" / "decision-trace.jsonl").read_text().strip().splitlines()
    approval_entries = (storage_root / "ledgers" / "approval-ledger.jsonl").read_text().strip().splitlines()
    assert len(trace_entries) >= 5
    assert len(approval_entries) == 1


def test_cli_rejects_invalid_state_transitions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code = main(["task", "create", "--title", "Guard rails", "--description", "Transition checks"])
    task_id = json.loads(capsys.readouterr().out)["task"]["id"]
    assert exit_code == 0

    exit_code = main(["run", "--task-id", task_id, "--runner", "grok_runner"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "plan" in captured.err

    exit_code = main(["approve", "--task-id", task_id, "--rationale", "Too early"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "review" in captured.err

    exit_code = main(["status", "--task-id", "task_missing"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "task_missing" in captured.err


def test_review_requires_completed_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code = main(["review", "--run-id", "run_missing", "--verdict", "fail", "--summary", "Missing run"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "run_missing" in captured.err


def test_builtin_local_runner_module_supports_shell_mode_and_persists_invocation_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))
    monkeypatch.setenv("PATCHRAIL_GROK_RUNNER_CMD", f"{sys.executable} -m patchrail.runners.local_harness")

    exit_code, created = run_cli(
        ["task", "create", "--title", "Shell runner", "--description", "Use configured command"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Use shell adapter", "--step", "Write manifest"],
        capsys,
    )
    assert exit_code == 0

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "grok_runner"], capsys)
    assert exit_code == 0
    run_id = executed["run"]["id"]
    assert executed["run"]["runner_assignment"]["mode"] == "shell"
    assert "python3" in executed["run"]["runner_assignment"]["command"]
    assert executed["run"]["exit_code"] == 0

    workspace_path = Path(executed["run"]["workspace_path"])
    assert (workspace_path / "output.json").exists()

    exit_code, logs_payload = run_cli(["logs", "--run-id", run_id], capsys)
    assert exit_code == 0
    assert "local harness stdout" in logs_payload["stdout"]

    exit_code, artifacts_payload = run_cli(["artifacts", "--run-id", run_id], capsys)
    assert exit_code == 0
    invocation_path = Path(artifacts_payload["artifact_bundle"]["files"]["invocation"])
    invocation = json.loads(invocation_path.read_text())
    assert invocation["mode"] == "shell"
    assert "patchrail.runners.local_harness" in invocation["command"]
    trace_path = Path(artifacts_payload["artifact_bundle"]["files"]["trace"])
    trace = json.loads(trace_path.read_text())
    assert trace["runner_name"] == "grok_runner"
    assert trace["schema_version"] == "patchrail.runner_trace.v1"


def test_local_smoke_script_completes_full_flow(tmp_path: Path) -> None:
    patchrail_home = tmp_path / ".patchrail-smoke"
    result = subprocess.run(
        ["/bin/sh", "scripts/local_smoke_test.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env={
            **os.environ.copy(),
            "PATCHRAIL_HOME": str(patchrail_home),
            "PYTHON_BIN": sys.executable,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "approved" in result.stdout
    assert patchrail_home.exists()


def test_real_preset_flow_can_complete_after_fallback_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-real"))
    monkeypatch.setattr("patchrail.core.preflight._command_exists", lambda command: True)

    def fake_run_status_command(command: list[str]) -> tuple[int, str, str]:
        if command == ["claude", "auth", "status"]:
            return (0, '{"loggedIn": true, "subscriptionType": "pro"}', "")
        if command == ["codex", "login", "status"]:
            return (0, "Logged in using ChatGPT", "")
        return (1, "", "unsupported")

    monkeypatch.setattr("patchrail.core.preflight._run_status_command", fake_run_status_command, raising=False)

    exit_code, _ = run_cli(["config", "init", "--preset", "real"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "Real preset smoke", "--description", "Exercise live readiness flow"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Use real preset", "--step", "Resolve planner"],
        capsys,
    )
    assert exit_code == 0
    assert planned["plan"]["resolved_assignment"]["provider"] == "claude"

    exit_code = main(["run", "--task-id", task_id, "--runner", "auto"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "approve-fallback" in captured.err

    exit_code, fallback_payload = run_cli(
        ["approve-fallback", "--task-id", task_id, "--rationale", "Allow real preset executor fallback"],
        capsys,
    )
    assert exit_code == 0
    assert fallback_payload["fallback_request"]["status"] == "approved"

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "auto"], capsys)
    assert exit_code == 0
    run_id = executed["run"]["id"]
    assert executed["run"]["resolved_assignment"]["provider"] == "claude"
    assert executed["run"]["fallback_event"]["selected_candidate"] == "claude_subscription_executor"

    exit_code, reviewed = run_cli(
        ["review", "--run-id", run_id, "--verdict", "pass", "--summary", "Reviewed under real preset"],
        capsys,
    )
    assert exit_code == 0
    assert reviewed["review"]["resolved_assignment"]["provider"] == "codex"

    exit_code, approved = run_cli(
        ["approve", "--task-id", task_id, "--rationale", "Real preset local flow passed"],
        capsys,
    )
    assert exit_code == 0
    assert approved["task"]["state"] == "approved"


def test_run_can_use_api_executor_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-api"))
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setattr("patchrail.core.preflight._command_exists", lambda command: True)

    def fake_run_status_command(command: list[str]) -> tuple[int, str, str]:
        if command == ["claude", "auth", "status"]:
            return (0, '{"loggedIn": true, "subscriptionType": "pro"}', "")
        if command == ["codex", "login", "status"]:
            return (0, "Logged in using ChatGPT", "")
        return (1, "", "unsupported")

    monkeypatch.setattr("patchrail.core.preflight._run_status_command", fake_run_status_command, raising=False)

    class FakeApiRunner:
        name = "grok_runner"
        mode = "api"
        command = "provider-api:grok"

        def run(self, task, plan, workspace_path, run_id):  # noqa: ANN001
            return RunnerResult(
                stdout="api runner stdout\n",
                stderr="",
                execution_summary="# API Execution Summary\n",
                diff_summary="- API diff summary\n",
                cost_metrics=CostMetrics(
                    prompt_tokens=21,
                    completion_tokens=34,
                    estimated_usd=0.12,
                    elapsed_seconds=1.5,
                ),
                exit_code=0,
            )

    monkeypatch.setattr("patchrail.core.service.build_api_runner", lambda candidate, runner_name: FakeApiRunner(), raising=False)

    exit_code, _ = run_cli(["config", "init", "--preset", "real"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "API path", "--description", "Use executor api path"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Plan before api run", "--step", "Plan"],
        capsys,
    )
    assert exit_code == 0

    exit_code, executed = run_cli(
        ["run", "--task-id", task_id, "--runner", "grok_runner", "--access-mode", "api"],
        capsys,
    )
    assert exit_code == 0
    assert executed["run"]["resolved_assignment"]["provider"] == "grok"
    assert executed["run"]["resolved_assignment"]["access_mode"] == "api"
    assert executed["run"]["runner_assignment"]["mode"] == "api"
    assert executed["run"]["runner_assignment"]["command"] == "provider-api:grok"


def test_run_can_use_subscription_executor_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-subscription"))
    monkeypatch.setattr("patchrail.core.preflight._command_exists", lambda command: True)

    def fake_run_status_command(command: list[str]) -> tuple[int, str, str]:
        if command == ["claude", "auth", "status"]:
            return (0, '{"loggedIn": true, "subscriptionType": "pro"}', "")
        if command == ["codex", "login", "status"]:
            return (0, "Logged in using ChatGPT", "")
        return (1, "", "unsupported")

    monkeypatch.setattr("patchrail.core.preflight._run_status_command", fake_run_status_command, raising=False)

    class FakeSubscriptionRunner:
        name = "claude_code"
        mode = "subscription"
        command = "provider-subscription:claude"

        def run(self, task, plan, workspace_path, run_id):  # noqa: ANN001
            return RunnerResult(
                stdout="subscription runner stdout\n",
                stderr="",
                execution_summary="# Subscription Execution Summary\n",
                diff_summary="- Subscription diff summary\n",
                cost_metrics=CostMetrics(
                    prompt_tokens=12,
                    completion_tokens=18,
                    estimated_usd=0.03,
                    elapsed_seconds=2.0,
                ),
                exit_code=0,
            )

    monkeypatch.setattr(
        "patchrail.core.service.build_subscription_runner",
        lambda candidate, runner_name: FakeSubscriptionRunner(),
        raising=False,
    )

    exit_code, _ = run_cli(["config", "init", "--preset", "real"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "Subscription path", "--description", "Use executor subscription path"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Plan before subscription run", "--step", "Plan"],
        capsys,
    )
    assert exit_code == 0

    exit_code, executed = run_cli(
        ["run", "--task-id", task_id, "--runner", "claude_code", "--access-mode", "subscription"],
        capsys,
    )
    assert exit_code == 0
    assert executed["run"]["resolved_assignment"]["provider"] == "claude"
    assert executed["run"]["resolved_assignment"]["access_mode"] == "subscription"
    assert executed["run"]["runner_assignment"]["mode"] == "subscription"
    assert executed["run"]["runner_assignment"]["command"] == "provider-subscription:claude"


def test_plan_and_review_support_auto_generation_in_local_preset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-auto"))

    exit_code, _ = run_cli(["config", "init"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "Auto flow", "--description", "Generate plan and review automatically"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(["plan", "--task-id", task_id, "--auto"], capsys)
    assert exit_code == 0
    assert planned["plan"]["resolved_assignment"]["role"] == "planner"
    assert planned["plan"]["summary"]
    assert planned["plan"]["steps"]

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "claude_code"], capsys)
    assert exit_code == 0
    run_id = executed["run"]["id"]

    exit_code, reviewed = run_cli(["review", "--run-id", run_id, "--auto"], capsys)
    assert exit_code == 0
    assert reviewed["review"]["resolved_assignment"]["role"] == "reviewer"
    assert reviewed["review"]["verdict"] in {"pass", "fail"}
    assert reviewed["review"]["summary"]


def test_plan_auto_can_use_subscription_planner_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-plan-auto-real"))
    monkeypatch.setattr("patchrail.core.preflight._command_exists", lambda command: True)

    def fake_run_status_command(command: list[str]) -> tuple[int, str, str]:
        if command == ["claude", "auth", "status"]:
            return (0, '{"loggedIn": true, "subscriptionType": "pro"}', "")
        if command == ["codex", "login", "status"]:
            return (0, "Logged in using ChatGPT", "")
        return (1, "", "unsupported")

    monkeypatch.setattr("patchrail.core.preflight._run_status_command", fake_run_status_command, raising=False)

    class FakeWorkflowEngine:
        backend_name = "fake-workflow"

        def generate_plan(self, candidate, task):  # noqa: ANN001
            return type(
                "PlanWorkflowResult",
                (),
                {
                    "summary": "Auto subscription plan",
                    "steps": ["Inspect task", "Prepare bounded execution"],
                    "metadata": {"backend": self.backend_name},
                },
            )()

        def generate_review(self, candidate, task, plan, run, bundle):  # noqa: ANN001
            raise AssertionError("review workflow should not be used in this test")

    monkeypatch.setattr("patchrail.core.service.build_workflow_engine", lambda store: FakeWorkflowEngine(), raising=False)

    exit_code, _ = run_cli(["config", "init", "--preset", "real"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "Auto plan real", "--description", "Use subscription planner path"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(["plan", "--task-id", task_id, "--auto"], capsys)
    assert exit_code == 0
    assert planned["plan"]["summary"] == "Auto subscription plan"
    assert planned["plan"]["resolved_assignment"]["provider"] == "claude"
    assert planned["plan"]["resolved_assignment"]["access_mode"] == "subscription"


def test_auto_plan_and_review_use_workflow_engine_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-workflows"))

    class FakeWorkflowEngine:
        backend_name = "fake-workflow"

        def generate_plan(self, candidate, task):  # noqa: ANN001
            return type(
                "PlanWorkflowResult",
                (),
                {
                    "summary": "Workflow-generated plan",
                    "steps": ["Ask the workflow engine"],
                    "metadata": {"backend": self.backend_name, "task_id": task.id},
                },
            )()

        def generate_review(self, candidate, task, plan, run, bundle):  # noqa: ANN001
            return type(
                "ReviewWorkflowResult",
                (),
                {
                    "verdict": ReviewVerdict.FAIL,
                    "summary": "Workflow-generated review",
                    "metadata": {"backend": self.backend_name, "run_id": run.id},
                },
            )()

    monkeypatch.setattr(
        "patchrail.core.service.build_workflow_engine",
        lambda store: FakeWorkflowEngine(),
        raising=False,
    )

    exit_code, _ = run_cli(["config", "init"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "Workflow seam", "--description", "Auto plan/review should use workflow engine"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(["plan", "--task-id", task_id, "--auto"], capsys)
    assert exit_code == 0
    assert planned["plan"]["summary"] == "Workflow-generated plan"
    assert planned["plan"]["steps"] == ["Ask the workflow engine"]
    assert planned["plan"]["workflow_backend"] == "fake-workflow"
    assert planned["plan"]["workflow_metadata"]["task_id"] == task_id

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "claude_code"], capsys)
    assert exit_code == 0
    run_id = executed["run"]["id"]

    exit_code, reviewed = run_cli(["review", "--run-id", run_id, "--auto"], capsys)
    assert exit_code == 0
    assert reviewed["review"]["verdict"] == "fail"
    assert reviewed["review"]["summary"] == "Workflow-generated review"
    assert reviewed["review"]["workflow_backend"] == "fake-workflow"
    assert reviewed["review"]["workflow_metadata"]["run_id"] == run_id


def test_plan_auto_surfaces_workflow_backend_initialization_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-langgraph"))
    monkeypatch.setenv("PATCHRAIL_WORKFLOW_BACKEND", "langgraph")

    monkeypatch.setattr(
        "patchrail.core.service.build_workflow_engine",
        lambda store: (_ for _ in ()).throw(
            PatchrailError("LangGraph workflow backend requires the optional 'langgraph' dependency.")
        ),
        raising=False,
    )

    exit_code, _ = run_cli(["config", "init"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "LangGraph optional", "--description", "Surface missing dependency clearly"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code = main(["plan", "--task-id", task_id, "--auto"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "langgraph" in captured.err.lower()
    assert "optional" in captured.err.lower()


def test_config_init_can_persist_langgraph_workflow_backend_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-workflow-config"))

    class FakeLangGraphWorkflowEngine:
        backend_name = "langgraph"

        def generate_plan(self, candidate, task):  # noqa: ANN001
            return type(
                "PlanWorkflowResult",
                (),
                {
                    "summary": "LangGraph-configured plan",
                    "steps": ["Run planner graph"],
                    "metadata": {"graph": "planner"},
                },
            )()

        def generate_review(self, candidate, task, plan, run, bundle):  # noqa: ANN001
            raise AssertionError("review workflow should not be used in this test")

    fake_module = type("FakeModule", (), {"LangGraphWorkflowEngine": FakeLangGraphWorkflowEngine})
    monkeypatch.setattr("patchrail.workflows.importlib.import_module", lambda name: fake_module, raising=False)

    exit_code, config_payload = run_cli(["config", "init", "--workflow-backend", "langgraph"], capsys)
    assert exit_code == 0
    assert config_payload["workflow"]["backend"] == "langgraph"
    assert Path(config_payload["workflow"]["path"]).exists()

    exit_code, created = run_cli(
        ["task", "create", "--title", "Configurable workflow backend", "--description", "Persist langgraph backend"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(["plan", "--task-id", task_id, "--auto"], capsys)
    assert exit_code == 0
    assert planned["plan"]["summary"] == "LangGraph-configured plan"
    assert planned["plan"]["workflow_backend"] == "langgraph"
    assert planned["plan"]["workflow_metadata"]["graph"] == "planner"


def test_env_workflow_backend_overrides_persisted_config_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail-workflow-config-override"))

    class FakeLangGraphWorkflowEngine:
        backend_name = "langgraph"

        def generate_plan(self, candidate, task):  # noqa: ANN001
            return type(
                "PlanWorkflowResult",
                (),
                {
                    "summary": "Env-selected LangGraph plan",
                    "steps": ["Use env override"],
                    "metadata": {"selected_by": "env"},
                },
            )()

        def generate_review(self, candidate, task, plan, run, bundle):  # noqa: ANN001
            raise AssertionError("review workflow should not be used in this test")

    fake_module = type("FakeModule", (), {"LangGraphWorkflowEngine": FakeLangGraphWorkflowEngine})
    monkeypatch.setattr("patchrail.workflows.importlib.import_module", lambda name: fake_module, raising=False)

    exit_code, config_payload = run_cli(["config", "init", "--workflow-backend", "local"], capsys)
    assert exit_code == 0
    assert config_payload["workflow"]["backend"] == "local"

    monkeypatch.setenv("PATCHRAIL_WORKFLOW_BACKEND", "langgraph")

    exit_code, created = run_cli(
        ["task", "create", "--title", "Env override", "--description", "Env should beat persisted config"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(["plan", "--task-id", task_id, "--auto"], capsys)
    assert exit_code == 0
    assert planned["plan"]["summary"] == "Env-selected LangGraph plan"
    assert planned["plan"]["workflow_backend"] == "langgraph"
    assert planned["plan"]["workflow_metadata"]["selected_by"] == "env"


def test_list_commands_return_tasks_runs_and_approvals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code, _ = run_cli(["config", "init"], capsys)
    assert exit_code == 0

    exit_code, first = run_cli(
        ["task", "create", "--title", "First task", "--description", "List coverage one"],
        capsys,
    )
    assert exit_code == 0
    first_task_id = first["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", first_task_id, "--summary", "Plan one", "--step", "Do one"],
        capsys,
    )
    assert exit_code == 0

    exit_code, executed = run_cli(["run", "--task-id", first_task_id, "--runner", "claude_code"], capsys)
    assert exit_code == 0
    first_run_id = executed["run"]["id"]

    exit_code, reviewed = run_cli(
        ["review", "--run-id", first_run_id, "--verdict", "pass", "--summary", "Approved run"],
        capsys,
    )
    assert exit_code == 0

    exit_code, approved = run_cli(["approve", "--task-id", first_task_id, "--rationale", "Accept"], capsys)
    assert exit_code == 0
    first_approval_id = approved["approval"]["id"]

    exit_code, second = run_cli(
        ["task", "create", "--title", "Second task", "--description", "List coverage two"],
        capsys,
    )
    assert exit_code == 0

    exit_code, tasks_payload = run_cli(["list", "tasks"], capsys)
    assert exit_code == 0
    task_ids = [task["id"] for task in tasks_payload["tasks"]]
    assert task_ids == [second["task"]["id"], first_task_id]

    exit_code, runs_payload = run_cli(["list", "runs", "--task-id", first_task_id], capsys)
    assert exit_code == 0
    assert [run["id"] for run in runs_payload["runs"]] == [first_run_id]

    exit_code, approvals_payload = run_cli(["list", "approvals", "--task-id", first_task_id], capsys)
    assert exit_code == 0
    assert [approval["id"] for approval in approvals_payload["approvals"]] == [first_approval_id]
    assert approvals_payload["approvals"][0]["review_id"] == reviewed["review"]["id"]


def test_list_commands_return_plans_and_reviews(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code, _ = run_cli(["config", "init"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "List plan review", "--description", "Inspect records"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Plan listing", "--step", "List plan"],
        capsys,
    )
    assert exit_code == 0
    plan_id = planned["plan"]["id"]

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "claude_code"], capsys)
    assert exit_code == 0
    run_id = executed["run"]["id"]

    exit_code, reviewed = run_cli(
        ["review", "--run-id", run_id, "--verdict", "pass", "--summary", "List review"],
        capsys,
    )
    assert exit_code == 0
    review_id = reviewed["review"]["id"]

    exit_code, plans_payload = run_cli(["list", "plans", "--task-id", task_id], capsys)
    assert exit_code == 0
    assert [plan["id"] for plan in plans_payload["plans"]] == [plan_id]

    exit_code, reviews_payload = run_cli(["list", "reviews", "--task-id", task_id], capsys)
    assert exit_code == 0
    assert [review["id"] for review in reviews_payload["reviews"]] == [review_id]
