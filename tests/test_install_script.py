from __future__ import annotations

import subprocess
from pathlib import Path


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
    assert f"pipx install --force --python python3.13 --editable {REPO_ROOT}" in completed.stdout
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
    assert "pipx inject patchrail langgraph" in completed.stdout
