from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from patchrail.cli.main import main


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
    assert "invocation" in artifact_paths
    invocation = json.loads(artifact_paths["invocation"].read_text())
    assert invocation["mode"] == "shell"
    assert "patchrail.runners.local_harness" in invocation["command"]
    assert invocation["workspace_path"] == str(workspace_path)

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
