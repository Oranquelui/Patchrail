from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = REPO_ROOT / "scripts" / "install_cli.sh"


def test_install_script_dry_run_prints_base_pipx_install_command() -> None:
    completed = subprocess.run(
        ["/bin/sh", str(INSTALL_SCRIPT), "--dry-run", "--python", "python3.13"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    assert "(cd " in completed.stdout
    assert "pipx uninstall patchrail" in completed.stdout
    assert f"pipx install --python python3.13 --editable {REPO_ROOT}" in completed.stdout
    assert "patchrail --help" in completed.stdout


def test_install_script_dry_run_prints_langgraph_injection_command() -> None:
    completed = subprocess.run(
        ["/bin/sh", str(INSTALL_SCRIPT), "--dry-run", "--python", "python3.13", "--with-langgraph"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "pipx uninstall patchrail" in completed.stdout
    assert "pipx inject patchrail langgraph" in completed.stdout


def test_install_script_runs_pipx_from_safe_directory_and_reinstalls_when_present(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    log_path = tmp_path / "pipx.log"
    python_path = fake_bin / "python3.13"
    pipx_path = fake_bin / "pipx"

    python_path.write_text("#!/bin/sh\nexit 0\n")
    python_path.chmod(0o755)
    pipx_path.write_text(
        """#!/bin/sh
set -eu
printf '%s|%s\\n' "$PWD" "$*" >> "$PIPX_LOG"
if [ "${1:-}" = "list" ] && [ "${2:-}" = "--json" ]; then
  printf '%s\\n' '{"venvs":{"patchrail":{"metadata":{"main_package":{"package":"patchrail"}}}}}'
  exit 0
fi
exit 0
"""
    )
    pipx_path.chmod(0o755)

    completed = subprocess.run(
        ["/bin/sh", str(INSTALL_SCRIPT), "--python", "python3.13", "--with-langgraph"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={
            "HOME": str(home_dir),
            "PATH": f"{fake_bin}:{Path('/usr/bin')}:{Path('/bin')}",
            "PIPX_LOG": str(log_path),
        },
    )

    assert completed.returncode == 0, completed.stderr
    log_lines = log_path.read_text().strip().splitlines()
    assert log_lines == [
        f"{home_dir}|uninstall patchrail",
        f"{home_dir}|install --python python3.13 --editable {REPO_ROOT}",
        f"{home_dir}|inject patchrail langgraph",
    ]
