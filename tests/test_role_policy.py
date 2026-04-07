from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from patchrail.cli.main import main


def run_cli(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, object]]:
    exit_code = main(args)
    captured = capsys.readouterr()
    payload = json.loads(captured.out) if captured.out.strip() else {}
    return exit_code, payload


def test_config_init_and_preflight_report_role_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code, config_payload = run_cli(["config", "init"], capsys)
    assert exit_code == 0
    config_path = Path(config_payload["config"]["path"])
    assert config_path.exists()

    exit_code, preflight_payload = run_cli(["preflight", "--role", "planner"], capsys)
    assert exit_code == 0
    assert preflight_payload["role"] == "planner"
    assert preflight_payload["selected_candidate"]["provider"] == "claude"
    assert preflight_payload["selected_candidate"]["access_mode"] == "subscription"
    assert len(preflight_payload["results"]) >= 2


def test_config_init_real_preset_writes_live_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code, config_payload = run_cli(["config", "init", "--preset", "real"], capsys)
    assert exit_code == 0

    config_path = Path(config_payload["config"]["path"])
    config = json.loads(config_path.read_text())

    planner_candidate = config["roles"]["planner"]["candidates"][0]
    executor_candidate = config["roles"]["executor"]["candidates"][0]

    assert planner_candidate["name"] == "claude_subscription_planner"
    assert planner_candidate["cli_command"] == "claude"
    assert planner_candidate["simulation"] is False
    assert planner_candidate["command"] == f"{sys.executable} -m patchrail.runners.local_harness"
    assert executor_candidate["name"] == "grok_subscription_executor"
    assert executor_candidate["cli_command"] == "grok"


def test_real_preset_preflight_uses_provider_status_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    monkeypatch.setattr("patchrail.core.preflight._command_exists", lambda command: True)

    def fake_run_status_command(command: list[str]) -> tuple[int, str, str]:
        if command == ["claude", "auth", "status"]:
            return (0, '{"loggedIn": true, "subscriptionType": "pro"}', "")
        if command == ["codex", "login", "status"]:
            return (0, "Logged in using ChatGPT", "")
        if command == ["grok", "auth", "status"]:
            return (0, '{"loggedIn": true}', "")
        return (1, "", "unsupported")

    monkeypatch.setattr("patchrail.core.preflight._run_status_command", fake_run_status_command, raising=False)

    exit_code, _ = run_cli(["config", "init", "--preset", "real"], capsys)
    assert exit_code == 0

    exit_code, preflight_payload = run_cli(["preflight", "--role", "executor"], capsys)
    assert exit_code == 0
    assert preflight_payload["selected_candidate"]["provider"] == "claude"
    assert preflight_payload["selected_candidate"]["access_mode"] == "subscription"

    grok_result = preflight_payload["results"][0]
    noninteractive_check = next(
        check for check in grok_result["checks"] if check["name"] == "noninteractive_ok"
    )
    assert grok_result["candidate_name"] == "grok_subscription_executor"
    assert grok_result["ready"] is False
    assert noninteractive_check["passed"] is False


def test_preflight_can_filter_by_access_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setattr("patchrail.core.preflight._command_exists", lambda command: True)
    monkeypatch.setattr(
        "patchrail.core.preflight._run_status_command",
        lambda command: (0, '{"loggedIn": true, "subscriptionType": "pro"}', ""),
        raising=False,
    )

    exit_code, _ = run_cli(["config", "init", "--preset", "real"], capsys)
    assert exit_code == 0

    exit_code, preflight_payload = run_cli(
        ["preflight", "--role", "executor", "--runner", "grok_runner", "--access-mode", "api"],
        capsys,
    )
    assert exit_code == 0
    assert preflight_payload["selected_candidate"]["provider"] == "grok"
    assert preflight_payload["selected_candidate"]["access_mode"] == "api"
    assert len(preflight_payload["results"]) == 1


def test_plan_review_and_run_persist_resolved_assignments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))

    exit_code, _ = run_cli(["config", "init"], capsys)
    assert exit_code == 0

    exit_code, created = run_cli(
        ["task", "create", "--title", "Role aware flow", "--description", "Persist resolved assignments"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, planned = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Create role-aware plan", "--step", "Resolve planner"],
        capsys,
    )
    assert exit_code == 0
    assert planned["plan"]["resolved_assignment"]["role"] == "planner"
    assert planned["plan"]["resolved_assignment"]["provider"] == "claude"

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "grok_runner"], capsys)
    assert exit_code == 0
    run_id = executed["run"]["id"]
    assert executed["run"]["resolved_assignment"]["role"] == "executor"
    assert executed["run"]["resolved_assignment"]["provider"] == "grok"

    exit_code, reviewed = run_cli(
        ["review", "--run-id", run_id, "--verdict", "pass", "--summary", "Resolved reviewer"],
        capsys,
    )
    assert exit_code == 0
    assert reviewed["review"]["resolved_assignment"]["role"] == "reviewer"
    assert reviewed["review"]["resolved_assignment"]["provider"] == "codex"


def test_cross_provider_fallback_creates_pending_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / ".patchrail"
    monkeypatch.setenv("PATCHRAIL_HOME", str(root))

    exit_code, config_payload = run_cli(["config", "init"], capsys)
    assert exit_code == 0
    config_path = Path(config_payload["config"]["path"])
    config = json.loads(config_path.read_text())
    config["roles"]["executor"]["candidates"] = [
        {
            "name": "grok_api_primary",
            "provider": "grok",
            "access_mode": "api",
            "capabilities": ["execution", "json_output"],
            "api_key_env": "PATCHRAIL_GROK_API_KEY",
            "endpoint_env": "PATCHRAIL_GROK_API_BASE",
            "command": f"{sys.executable} -m patchrail.runners.local_harness"
        },
        {
            "name": "codex_subscription_fallback",
            "provider": "codex",
            "access_mode": "subscription",
            "capabilities": ["execution", "json_output", "noninteractive"],
            "command": f"{sys.executable} -m patchrail.runners.local_harness",
            "simulation": True
        }
    ]
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    exit_code, created = run_cli(
        ["task", "create", "--title", "Fallback guard", "--description", "Require approval"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Plan before guarded run", "--step", "Plan"],
        capsys,
    )
    assert exit_code == 0

    exit_code = main(["run", "--task-id", task_id, "--runner", "auto"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "approval" in captured.err.lower()
    assert "approve-fallback" in captured.err

    exit_code, status_payload = run_cli(["status", "--task-id", task_id], capsys)
    assert exit_code == 0
    request = status_payload["latest_fallback_request"]
    assert request["task_id"] == task_id
    assert request["status"] == "pending"
    assert request["role"] == "executor"
    assert request["requested_assignment"]["provider"] == "codex"


def test_approved_fallback_allows_retry_to_proceed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / ".patchrail"
    monkeypatch.setenv("PATCHRAIL_HOME", str(root))

    exit_code, config_payload = run_cli(["config", "init"], capsys)
    assert exit_code == 0
    config_path = Path(config_payload["config"]["path"])
    config = json.loads(config_path.read_text())
    config["roles"]["executor"]["candidates"] = [
        {
            "name": "grok_api_primary",
            "provider": "grok",
            "access_mode": "api",
            "capabilities": ["execution", "json_output"],
            "api_key_env": "PATCHRAIL_GROK_API_KEY",
            "endpoint_env": "PATCHRAIL_GROK_API_BASE",
            "command": f"{sys.executable} -m patchrail.runners.local_harness"
        },
        {
            "name": "codex_subscription_fallback",
            "provider": "codex",
            "access_mode": "subscription",
            "capabilities": ["execution", "json_output", "noninteractive"],
            "command": f"{sys.executable} -m patchrail.runners.local_harness",
            "simulation": True
        }
    ]
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    exit_code, created = run_cli(
        ["task", "create", "--title", "Fallback approval", "--description", "Explicitly allow deviation"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Plan before approved run", "--step", "Plan"],
        capsys,
    )
    assert exit_code == 0

    exit_code = main(["run", "--task-id", task_id, "--runner", "auto"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "approve-fallback" in captured.err

    exit_code, approved = run_cli(
        ["approve-fallback", "--task-id", task_id, "--rationale", "Allow cross-provider fallback"],
        capsys,
    )
    assert exit_code == 0
    assert approved["fallback_request"]["status"] == "approved"

    exit_code, executed = run_cli(["run", "--task-id", task_id, "--runner", "auto"], capsys)
    assert exit_code == 0
    assert executed["run"]["resolved_assignment"]["provider"] == "codex"


def test_list_fallback_requests_returns_latest_requests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / ".patchrail"
    monkeypatch.setenv("PATCHRAIL_HOME", str(root))

    exit_code, config_payload = run_cli(["config", "init"], capsys)
    assert exit_code == 0
    config_path = Path(config_payload["config"]["path"])
    config = json.loads(config_path.read_text())
    config["roles"]["executor"]["candidates"] = [
        {
            "name": "grok_api_primary",
            "provider": "grok",
            "access_mode": "api",
            "capabilities": ["execution", "json_output"],
            "api_key_env": "PATCHRAIL_GROK_API_KEY",
            "endpoint_env": "PATCHRAIL_GROK_API_BASE",
            "command": f"{sys.executable} -m patchrail.runners.local_harness"
        },
        {
            "name": "codex_subscription_fallback",
            "provider": "codex",
            "access_mode": "subscription",
            "capabilities": ["execution", "json_output", "noninteractive"],
            "command": f"{sys.executable} -m patchrail.runners.local_harness",
            "simulation": True
        }
    ]
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    exit_code, created = run_cli(
        ["task", "create", "--title", "Fallback list", "--description", "List fallback requests"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Plan before blocked run", "--step", "Plan"],
        capsys,
    )
    assert exit_code == 0

    exit_code = main(["run", "--task-id", task_id, "--runner", "auto"])
    capsys.readouterr()
    assert exit_code == 1

    exit_code, fallback_payload = run_cli(["list", "fallback-requests", "--task-id", task_id], capsys)
    assert exit_code == 0
    assert len(fallback_payload["fallback_requests"]) == 1
    assert fallback_payload["fallback_requests"][0]["task_id"] == task_id
    assert fallback_payload["fallback_requests"][0]["status"] == "pending"


def test_preflight_snapshots_are_persisted_and_listable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / ".patchrail"
    monkeypatch.setenv("PATCHRAIL_HOME", str(root))

    exit_code, config_payload = run_cli(["config", "init"], capsys)
    assert exit_code == 0
    config_path = Path(config_payload["config"]["path"])
    config = json.loads(config_path.read_text())
    config["roles"]["executor"]["candidates"] = [
        {
            "name": "grok_api_primary",
            "provider": "grok",
            "access_mode": "api",
            "capabilities": ["execution", "json_output"],
            "api_key_env": "PATCHRAIL_GROK_API_KEY",
            "endpoint_env": "PATCHRAIL_GROK_API_BASE",
            "command": f"{sys.executable} -m patchrail.runners.local_harness"
        },
        {
            "name": "codex_subscription_fallback",
            "provider": "codex",
            "access_mode": "subscription",
            "capabilities": ["execution", "json_output", "noninteractive"],
            "command": f"{sys.executable} -m patchrail.runners.local_harness",
            "simulation": True
        }
    ]
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    exit_code, created = run_cli(
        ["task", "create", "--title", "Snapshot task", "--description", "Persist snapshots"],
        capsys,
    )
    assert exit_code == 0
    task_id = created["task"]["id"]

    exit_code, _ = run_cli(
        ["plan", "--task-id", task_id, "--summary", "Snapshot plan", "--step", "Plan"],
        capsys,
    )
    assert exit_code == 0

    exit_code = main(["run", "--task-id", task_id, "--runner", "auto"])
    capsys.readouterr()
    assert exit_code == 1

    exit_code, snapshots_payload = run_cli(["list", "preflight-snapshots", "--task-id", task_id], capsys)
    assert exit_code == 0
    phases = [snapshot["phase"] for snapshot in snapshots_payload["preflight_snapshots"]]
    assert phases == ["run", "plan"]
    assert snapshots_payload["preflight_snapshots"][0]["fallback_event"]["selected_candidate"] == "codex_subscription_fallback"
