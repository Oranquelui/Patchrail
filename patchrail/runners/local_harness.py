from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    task_file = Path(_require_env("PATCHRAIL_TASK_FILE"))
    plan_file = Path(_require_env("PATCHRAIL_PLAN_FILE"))
    output_file = Path(_require_env("PATCHRAIL_OUTPUT_FILE"))
    run_id = _require_env("PATCHRAIL_RUN_ID")
    runner_name = os.getenv("PATCHRAIL_RUNNER_NAME", "local_harness")

    task = json.loads(task_file.read_text())
    plan = json.loads(plan_file.read_text())

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
        "runner_trace": {
            "schema_version": "patchrail.runner_trace.v1",
            "runner_name": runner_name,
            "run_id": run_id,
            "events": [
                {"name": "input.loaded", "status": "ok"},
                {"name": "output.persisted", "status": "ok"},
            ],
        },
    }
    output_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"local harness stdout for {task['id']} via {runner_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
