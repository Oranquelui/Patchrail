from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from patchrail.cli.main import main
from patchrail.core.layers import HARNESS_CONTRACT
from patchrail.core.layers import PLANNING_LAYER_SPECS
from patchrail.core import layers


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


def test_brief_schema_contract_declares_v1_boundary() -> None:
    assert hasattr(layers, "BRIEF_SCHEMA_CONTRACT")
    brief_schema_contract = layers.BRIEF_SCHEMA_CONTRACT
    assert brief_schema_contract.schema_version == "patchrail.brief_schema.v1"
    assert brief_schema_contract.owns_canonical_state is False
    assert brief_schema_contract.required_kinds == ["future", "ontology", "product"]
    assert brief_schema_contract.sequence == ["future", "ontology", "product"]
    assert brief_schema_contract.record_fields == [
        "id",
        "task_id",
        "kind",
        "schema_version",
        "source_path",
        "storage_path",
        "content",
        "sha256",
        "created_at",
        "attached_plan_id",
    ]


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


def test_evidence_bundle_contract_declares_v1_manifest_boundary() -> None:
    assert hasattr(layers, "EVIDENCE_BUNDLE_CONTRACT")
    evidence_bundle_contract = layers.EVIDENCE_BUNDLE_CONTRACT
    assert evidence_bundle_contract.schema_version == "patchrail.evidence_bundle.v1"
    assert evidence_bundle_contract.owns_canonical_state is False
    assert evidence_bundle_contract.phase == "after_executor_run_before_review"
    assert evidence_bundle_contract.required_logical_kinds == [
        "execution_summary",
        "diff_summary",
        "runner_stdout",
        "runner_stderr",
        "runner_invocation",
    ]
    assert evidence_bundle_contract.optional_logical_kinds == ["runner_trace", "runner_artifact"]


def test_runner_contract_declares_v1_workspace_and_env_boundary() -> None:
    assert hasattr(layers, "RUNNER_CONTRACT")
    runner_contract = layers.RUNNER_CONTRACT
    assert runner_contract.schema_version == "patchrail.runner_contract.v1"
    assert runner_contract.owns_canonical_state is False
    assert runner_contract.workspace_files == {
        "task": "task.json",
        "plan": "plan.json",
        "output": "output.json",
    }
    assert runner_contract.reserved_environment == [
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
    assert runner_contract.runner_writable_paths == [
        "output.json",
        "artifacts/",
        "trace.json",
    ]
    assert runner_contract.forbidden_ownership == [
        "task_lifecycle_state",
        "canonical_plan",
        "review_verdict",
        "approval_decision",
        "approval_ledger",
    ]


def test_cli_exposes_runner_contract_for_operator_inspection(capsys) -> None:
    exit_code, payload = run_cli(["contracts", "runner"], capsys)

    assert exit_code == 0
    contract = payload["runner_contract"]
    assert contract["schema_version"] == "patchrail.runner_contract.v1"
    assert contract["owns_canonical_state"] is False
    assert contract["workspace_files"] == {
        "task": "task.json",
        "plan": "plan.json",
        "output": "output.json",
    }
    assert "PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION" in contract["reserved_environment"]
    assert "PATCHRAIL_WORKSPACE" in contract["reserved_environment"]
    assert "PATCHRAIL_TRACE_FILE" in contract["reserved_environment"]
    assert contract["runner_writable_paths"] == ["output.json", "artifacts/", "trace.json"]
    assert contract["forbidden_ownership"] == [
        "task_lifecycle_state",
        "canonical_plan",
        "review_verdict",
        "approval_decision",
        "approval_ledger",
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
    assert "Schema: patchrail.brief_schema.v1" in templates["future"]
    assert "Timing: before implementation" in templates["future"]
    assert "Layer: reality_boundary" in templates["ontology"]
    assert "Schema: patchrail.brief_schema.v1" in templates["ontology"]
    assert "Timing: before implementation" in templates["ontology"]
    assert "Layer: post_implementation_acceptance" in templates["product"]
    assert "Schema: patchrail.brief_schema.v1" in templates["product"]
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
    workspace_path = tmp_path / "workspace"
    artifact_dir = workspace_path / "artifacts"
    task_file = workspace_path / "task.json"
    plan_file = workspace_path / "plan.json"
    output_file = workspace_path / "output.json"
    trace_file = workspace_path / "trace.json"
    workspace_path.mkdir()
    task_file.write_text(json.dumps({"id": "task_test", "title": "Harness", "description": "capture evidence"}))
    plan_file.write_text(json.dumps({"id": "plan_test", "summary": "Run the harness", "steps": ["execute"]}))

    result = subprocess.run(
        [sys.executable, "-m", "patchrail.runners.local_harness"],
            env={
                **os.environ.copy(),
                "PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION": "patchrail.runner_contract.v1",
                "PATCHRAIL_TASK_FILE": str(task_file),
                "PATCHRAIL_PLAN_FILE": str(plan_file),
                "PATCHRAIL_OUTPUT_FILE": str(output_file),
            "PATCHRAIL_RUN_ID": "run_test",
            "PATCHRAIL_RUNNER_NAME": "local_harness",
            "PATCHRAIL_WORKSPACE": str(workspace_path),
            "PATCHRAIL_ARTIFACT_DIR": str(artifact_dir),
            "PATCHRAIL_TRACE_FILE": str(trace_file),
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
    assert output["runner_trace"]["runner_contract"]["schema_version"] == "patchrail.runner_contract.v1"
    assert output["runner_trace"]["runner_contract"]["workspace_files"] == {
        "task": "task.json",
        "plan": "plan.json",
        "output": "output.json",
    }
    assert output["runner_trace"]["contract_runtime"] == {
        "reserved_environment_present": [
            "PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION",
            "PATCHRAIL_RUN_ID",
            "PATCHRAIL_RUNNER_NAME",
            "PATCHRAIL_WORKSPACE",
            "PATCHRAIL_TASK_FILE",
            "PATCHRAIL_PLAN_FILE",
            "PATCHRAIL_OUTPUT_FILE",
            "PATCHRAIL_ARTIFACT_DIR",
            "PATCHRAIL_TRACE_FILE",
        ],
        "workspace_relative_paths": {
            "task": "task.json",
            "plan": "plan.json",
            "output": "output.json",
            "artifacts": "artifacts",
            "trace": "trace.json",
        },
        "runner_contract_schema_version": "patchrail.runner_contract.v1",
        "runner_writable_paths_ready": ["output.json", "artifacts/", "trace.json"],
    }
    assert trace_file.exists()
    trace_payload = json.loads(trace_file.read_text())
    assert trace_payload["contract_runtime"] == output["runner_trace"]["contract_runtime"]
