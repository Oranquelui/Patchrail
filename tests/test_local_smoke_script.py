from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "local_smoke_test.sh"


def test_local_smoke_script_persists_v1_briefs_and_plan_references(tmp_path: Path) -> None:
    patchrail_home = tmp_path / ".patchrail"
    env = os.environ.copy()
    env.update(
        {
            "PATCHRAIL_HOME": str(patchrail_home),
            "PATCHRAIL_CONFIG_PRESET": "local",
            "PATCHRAIL_WORKFLOW_BACKEND": "local",
            "PYTHON_BIN": sys.executable,
        }
    )

    completed = subprocess.run(
        ["/bin/sh", str(SMOKE_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    brief_sequence = {"future": 0, "ontology": 1, "product": 2}
    brief_records = sorted(
        [
            json.loads(path.read_text())
            for path in sorted((patchrail_home / "briefs").glob("brief_*.json"))
        ],
        key=lambda brief: brief_sequence[brief["kind"]],
    )
    assert [brief["kind"] for brief in brief_records] == ["future", "ontology", "product"]
    assert {brief["schema_version"] for brief in brief_records} == {"patchrail.brief_schema.v1"}

    plan_records = [
        json.loads(path.read_text())
        for path in sorted((patchrail_home / "plans").glob("plan_*.json"))
    ]
    assert len(plan_records) == 1
    assert [brief["kind"] for brief in plan_records[0]["planning_briefs"]] == [
        "future",
        "ontology",
        "product",
    ]
    assert {brief["schema_version"] for brief in plan_records[0]["planning_briefs"]} == {
        "patchrail.brief_schema.v1"
    }

    run_records = [
        json.loads(path.read_text())
        for path in sorted((patchrail_home / "runs").glob("run_*.json"))
    ]
    assert len(run_records) == 1
    canonical_artifact_dir = patchrail_home / "artifacts" / run_records[0]["id"]
    bundle = json.loads((canonical_artifact_dir / "bundle.json").read_text())
    runner_artifact_key = "runner_artifact:local-harness-report.json"
    assert runner_artifact_key in bundle["artifacts"]
    runner_artifact = bundle["artifacts"][runner_artifact_key]
    assert runner_artifact["logical_kind"] == "runner_artifact"
    assert runner_artifact["media_type"] == "application/json"
    assert runner_artifact["collection_status"] == "collected"
    canonical_runner_artifact_path = canonical_artifact_dir / "runner-artifacts" / "local-harness-report.json"
    assert runner_artifact["path"] == str(canonical_runner_artifact_path)
    assert json.loads(canonical_runner_artifact_path.read_text())["runner_contract_schema_version"] == (
        "patchrail.runner_contract.v1"
    )

    trace = json.loads((canonical_artifact_dir / "trace.json").read_text())
    assert trace["runner_contract"]["schema_version"] == "patchrail.runner_contract.v1"
    assert trace["runner_contract"]["reserved_environment"] == [
        "PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION",
        "PATCHRAIL_RUN_ID",
        "PATCHRAIL_RUNNER_NAME",
        "PATCHRAIL_WORKSPACE",
        "PATCHRAIL_TASK_FILE",
        "PATCHRAIL_PLAN_FILE",
        "PATCHRAIL_OUTPUT_FILE",
        "PATCHRAIL_ARTIFACT_DIR",
        "PATCHRAIL_TRACE_FILE",
    ]
    assert trace["contract_runtime"]["workspace_relative_paths"] == {
        "task": "task.json",
        "plan": "plan.json",
        "output": "output.json",
        "artifacts": "artifacts",
        "trace": "trace.json",
    }
    assert "PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION" in trace["contract_runtime"][
        "reserved_environment_present"
    ]
    assert trace["contract_runtime"]["runner_contract_schema_version"] == "patchrail.runner_contract.v1"
    assert trace["contract_runtime"]["runner_writable_paths_ready"] == [
        "output.json",
        "artifacts/",
        "trace.json",
    ]
    assert "briefs=3" in completed.stdout
