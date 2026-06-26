from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from patchrail.core.layers import HARNESS_CONTRACT, RUNNER_CONTRACT


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _workspace_relative(path: Path, workspace_path: Path) -> str:
    try:
        return path.relative_to(workspace_path).as_posix()
    except ValueError:
        return str(path)


def _is_runner_writable_path_ready(workspace_path: Path, contract_path: str) -> bool:
    path = workspace_path / contract_path.rstrip("/")
    if contract_path.endswith("/"):
        return path.is_dir()
    return path.parent.is_dir()


def main() -> int:
    task_file = Path(_require_env("PATCHRAIL_TASK_FILE"))
    plan_file = Path(_require_env("PATCHRAIL_PLAN_FILE"))
    output_file = Path(_require_env("PATCHRAIL_OUTPUT_FILE"))
    run_id = _require_env("PATCHRAIL_RUN_ID")
    runner_name = os.getenv("PATCHRAIL_RUNNER_NAME", "local_harness")
    runner_contract_schema_version = os.getenv(
        "PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION", RUNNER_CONTRACT.schema_version
    )
    workspace_path = Path(os.getenv("PATCHRAIL_WORKSPACE", output_file.parent))
    artifact_dir = Path(os.getenv("PATCHRAIL_ARTIFACT_DIR", workspace_path / "artifacts"))
    trace_file = Path(os.getenv("PATCHRAIL_TRACE_FILE", workspace_path / "trace.json"))
    artifact_dir.mkdir(parents=True, exist_ok=True)

    task = json.loads(task_file.read_text())
    plan = json.loads(plan_file.read_text())
    contract_runtime = {
        "reserved_environment_present": [
            name for name in RUNNER_CONTRACT.reserved_environment if os.getenv(name)
        ],
        "workspace_relative_paths": {
            "task": _workspace_relative(task_file, workspace_path),
            "plan": _workspace_relative(plan_file, workspace_path),
            "output": _workspace_relative(output_file, workspace_path),
            "artifacts": _workspace_relative(artifact_dir, workspace_path),
            "trace": _workspace_relative(trace_file, workspace_path),
        },
        "runner_contract_schema_version": runner_contract_schema_version,
        "runner_writable_paths_ready": [
            path
            for path in RUNNER_CONTRACT.runner_writable_paths
            if _is_runner_writable_path_ready(workspace_path, path)
        ],
    }
    runner_trace = {
        "schema_version": "patchrail.runner_trace.v1",
        "harness_contract": HARNESS_CONTRACT.to_dict(),
        "runner_contract": RUNNER_CONTRACT.to_dict(),
        "contract_runtime": contract_runtime,
        "runner_name": runner_name,
        "run_id": run_id,
        "workspace": {
            "path": str(workspace_path),
            "task_file": str(task_file),
            "plan_file": str(plan_file),
            "output_file": str(output_file),
            "artifact_dir": str(artifact_dir),
            "trace_file": str(trace_file),
        },
        "events": [
            {"name": "input.loaded", "status": "ok"},
            {"name": "output.persisted", "status": "ok"},
        ],
    }
    harness_artifact = {
        "schema_version": "patchrail.local_harness_artifact.v1",
        "runner_contract_schema_version": RUNNER_CONTRACT.schema_version,
        "run_id": run_id,
        "runner_name": runner_name,
        "task_id": task["id"],
        "plan_id": plan["id"],
        "artifact_role": "runner_local_reproducibility_evidence",
    }
    (artifact_dir / "local-harness-report.json").write_text(
        json.dumps(harness_artifact, indent=2, sort_keys=True) + "\n"
    )

    payload = {
        "execution_summary": (
            "# Local Harness Execution\n\n"
            f"Runner: {runner_name}\n"
            f"Task: {task['id']}\n"
            f"Plan Summary: {plan['summary']}\n"
        ),
        "diff_summary": (
            "- Local harness produced a deterministic output payload.\n"
            "- This run is suitable for end-to-end local smoke testing.\n"
        ),
        "cost_metrics": {
            "prompt_tokens": 11,
            "completion_tokens": 13,
            "estimated_usd": 0.01,
            "elapsed_seconds": 0.2,
        },
        "runner_trace": runner_trace,
    }
    output_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    trace_file.write_text(json.dumps(runner_trace, indent=2, sort_keys=True) + "\n")
    print(f"local harness stdout for {task['id']} via {runner_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
