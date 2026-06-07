from __future__ import annotations

import json
import sys
from pathlib import Path

from patchrail.cli.main import main


def run_cli(args: list[str], capsys):
    exit_code = main(["--json", *args])
    captured = capsys.readouterr()
    payload = json.loads(captured.out) if captured.out.strip() else {}
    return exit_code, payload


def run_cli_text(args: list[str], capsys):
    exit_code = main(args)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def create_completed_run(tmp_path: Path, monkeypatch, capsys) -> tuple[str, str]:
    monkeypatch.setenv("PATCHRAIL_HOME", str(tmp_path / ".patchrail"))
    assert run_cli(["config", "init"], capsys)[0] == 0
    exit_code, task_payload = run_cli(
        ["task", "create", "--title", "Verify AI output", "--description", "Check generated code"],
        capsys,
    )
    assert exit_code == 0
    task_id = task_payload["task"]["id"]
    assert run_cli(
        [
            "plan",
            "--task-id",
            task_id,
            "--summary",
            "Run and verify the agent output",
            "--step",
            "Execute local harness",
        ],
        capsys,
    )[0] == 0
    exit_code, run_payload = run_cli(["run", "--task-id", task_id, "--runner", "auto"], capsys)
    assert exit_code == 0
    return task_id, run_payload["run"]["id"]


def test_verify_records_successful_command_and_lists_by_task_and_run(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    task_id, run_id = create_completed_run(tmp_path, monkeypatch, capsys)

    exit_code, payload = run_cli(
        [
            "verify",
            "--run-id",
            run_id,
            "--command",
            f'"{sys.executable}" -c "print(\'verification ok\')"',
        ],
        capsys,
    )

    assert exit_code == 0
    verification = payload["verification"]
    assert verification["task_id"] == task_id
    assert verification["run_id"] == run_id
    assert verification["status"] == "passed"
    assert verification["exit_code"] == 0
    assert verification["command"].endswith("print('verification ok')\"")
    assert Path(verification["stdout_path"]).read_text() == "verification ok\n"
    assert Path(verification["stderr_path"]).read_text() == ""

    assert run_cli(["list", "verifications", "--task-id", task_id], capsys)[1]["verifications"] == [verification]
    assert run_cli(["list", "verifications", "--run-id", run_id], capsys)[1]["verifications"] == [verification]


def test_verify_records_failed_command_without_crashing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _, run_id = create_completed_run(tmp_path, monkeypatch, capsys)

    exit_code, payload = run_cli(
        [
            "verify",
            "--run-id",
            run_id,
            "--command",
            f'"{sys.executable}" -c "import sys; print(\'bad\'); sys.exit(3)"',
        ],
        capsys,
    )

    assert exit_code == 0
    verification = payload["verification"]
    assert verification["status"] == "failed"
    assert verification["exit_code"] == 3
    assert Path(verification["stdout_path"]).read_text() == "bad\n"


def test_packet_show_and_export_include_verification_and_unresolved_gaps(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    task_id, run_id = create_completed_run(tmp_path, monkeypatch, capsys)
    assert run_cli(
        [
            "verify",
            "--run-id",
            run_id,
            "--command",
            f'"{sys.executable}" -c "print(\'verification ok\')"',
        ],
        capsys,
    )[0] == 0

    exit_code, stdout, stderr = run_cli_text(
        ["packet", "show", "--task-id", task_id, "--format", "markdown"],
        capsys,
    )

    assert exit_code == 0
    assert stderr == ""
    assert "# Patchrail Approval Packet" in stdout
    assert "## Delivery Contract" in stdout
    assert "## Verification" in stdout
    assert "passed" in stdout
    assert "No review recorded." in stdout
    assert "No approval decision recorded." in stdout

    output_path = tmp_path / "packet.md"
    exit_code, payload = run_cli(
        ["packet", "export", "--task-id", task_id, "--output", str(output_path), "--format", "markdown"],
        capsys,
    )

    assert exit_code == 0
    assert payload["output_path"] == str(output_path)
    assert output_path.read_text() == stdout


def test_review_queue_groups_tasks_by_latest_verification_status(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    ready_task_id, ready_run_id = create_completed_run(tmp_path, monkeypatch, capsys)
    assert run_cli(
        [
            "verify",
            "--run-id",
            ready_run_id,
            "--command",
            f'"{sys.executable}" -c "print(\'ok\')"',
        ],
        capsys,
    )[0] == 0

    needs_task_id, _ = create_completed_run(tmp_path, monkeypatch, capsys)
    failed_task_id, failed_run_id = create_completed_run(tmp_path, monkeypatch, capsys)
    assert run_cli(
        [
            "verify",
            "--run-id",
            failed_run_id,
            "--command",
            f'"{sys.executable}" -c "import sys; sys.exit(2)"',
        ],
        capsys,
    )[0] == 0

    exit_code, payload = run_cli(["list", "review-queue"], capsys)

    assert exit_code == 0
    queue = payload["review_queue"]
    assert [task["id"] for task in queue["ready_for_review"]] == [ready_task_id]
    assert [task["id"] for task in queue["needs_verification"]] == [needs_task_id]
    assert [task["id"] for task in queue["failed_verification"]] == [failed_task_id]
    assert queue["awaiting_approval"] == []
    assert queue["approved"] == []
