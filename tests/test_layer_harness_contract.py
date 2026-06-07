from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from patchrail.cli.main import main
from patchrail.core.layers import HARNESS_CONTRACT
from patchrail.core.layers import PLANNING_LAYER_SPECS


def run_cli(args: list[str], capsys):
    exit_code = main(["--json", *args])
    captured = capsys.readouterr()
    payload = json.loads(captured.out) if captured.out.strip() else {}
    return exit_code, payload


def test_planning_layers_are_ordered_by_purpose() -> None:
    assert [layer.kind for layer in PLANNING_LAYER_SPECS] == ["future", "ontology", "product"]
    assert [layer.layer for layer in PLANNING_LAYER_SPECS] == [
        "prediction",
        "reality_boundary",
        "post_implementation_acceptance",
    ]
    assert PLANNING_LAYER_SPECS[0].question == "What should be true in the future?"
    assert PLANNING_LAYER_SPECS[1].question == "What exists, who owns it, and where are the boundaries?"
    assert PLANNING_LAYER_SPECS[2].question == "What must be true after implementation for users and operators?"


def test_harness_contract_is_post_implementation_evidence_layer() -> None:
    assert HARNESS_CONTRACT.schema_version == "patchrail.harness_contract.v1"
    assert HARNESS_CONTRACT.layer == "post_implementation_evidence"
    assert HARNESS_CONTRACT.phase == "after_executor_run_before_review"
    assert HARNESS_CONTRACT.owns_canonical_state is False
    assert HARNESS_CONTRACT.captures == [
        "execution_summary",
        "diff_summary",
        "stdout",
        "stderr",
        "invocation",
        "runner_trace",
        "artifact_bundle",
    ]


def test_setup_project_templates_embed_layer_purpose_and_timing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    patchrail_home = tmp_path / ".patchrail"
    monkeypatch.setenv("PATCHRAIL_HOME", str(patchrail_home))

    exit_code, payload = run_cli(
        [
            "setup",
            "project",
            "--title",
            "Layered rollout",
            "--description",
            "Prove the Patchrail layer model",
        ],
        capsys,
    )

    assert exit_code == 0
    templates = {kind: Path(path).read_text() for kind, path in payload["setup"]["brief_files"].items()}
    assert "Layer: prediction" in templates["future"]
    assert "Timing: before implementation" in templates["future"]
    assert "Layer: reality_boundary" in templates["ontology"]
    assert "Timing: before implementation" in templates["ontology"]
    assert "Layer: post_implementation_acceptance" in templates["product"]
    assert "Timing: define before implementation; verify after implementation" in templates["product"]


def test_setup_project_guided_templates_frame_briefs_as_delivery_contract(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    patchrail_home = tmp_path / ".patchrail"
    monkeypatch.setenv("PATCHRAIL_HOME", str(patchrail_home))

    exit_code, payload = run_cli(
        [
            "setup",
            "project",
            "--title",
            "Review bottleneck",
            "--description",
            "Make AI generated changes easier to verify",
            "--guided",
        ],
        capsys,
    )

    assert exit_code == 0
    templates = {kind: Path(path).read_text() for kind, path in payload["setup"]["brief_files"].items()}
    assert "Delivery Contract" in templates["future"]
    assert "What exact future state should the AI-coded change produce?" in templates["future"]
    assert "What business or product rule would make a passing test still wrong?" in templates["ontology"]
    assert "What evidence must the approval packet show before a human can approve?" in templates["product"]
    assert payload["setup"]["guided"] is True


def test_local_harness_trace_declares_harness_contract(tmp_path: Path) -> None:
    task_file = tmp_path / "task.json"
    plan_file = tmp_path / "plan.json"
    output_file = tmp_path / "output.json"
    task_file.write_text(json.dumps({"id": "task_test", "title": "Harness", "description": "capture evidence"}))
    plan_file.write_text(json.dumps({"id": "plan_test", "summary": "Run the harness", "steps": ["execute"]}))

    result = subprocess.run(
        [sys.executable, "-m", "patchrail.runners.local_harness"],
        env={
            **os.environ.copy(),
            "PATCHRAIL_TASK_FILE": str(task_file),
            "PATCHRAIL_PLAN_FILE": str(plan_file),
            "PATCHRAIL_OUTPUT_FILE": str(output_file),
            "PATCHRAIL_RUN_ID": "run_test",
            "PATCHRAIL_RUNNER_NAME": "local_harness",
        },
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    output = json.loads(output_file.read_text())
    assert output["runner_trace"]["harness_contract"] == {
        "schema_version": "patchrail.harness_contract.v1",
        "layer": "post_implementation_evidence",
        "phase": "after_executor_run_before_review",
        "owns_canonical_state": False,
        "captures": [
            "execution_summary",
            "diff_summary",
            "stdout",
            "stderr",
            "invocation",
            "runner_trace",
            "artifact_bundle",
        ],
    }
