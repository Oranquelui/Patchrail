from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class PlanningLayerSpec:
    kind: str
    layer: str
    title: str
    question: str
    timing: str
    purpose: str
    headings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HarnessContract:
    schema_version: str
    layer: str
    phase: str
    owns_canonical_state: bool
    captures: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BriefSchemaContract:
    schema_version: str
    owns_canonical_state: bool
    required_kinds: list[str]
    sequence: list[str]
    record_fields: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceBundleContract:
    schema_version: str
    owns_canonical_state: bool
    phase: str
    required_logical_kinds: list[str]
    optional_logical_kinds: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RunnerContract:
    schema_version: str
    owns_canonical_state: bool
    workspace_files: dict[str, str]
    reserved_environment: list[str]
    runner_writable_paths: list[str]
    forbidden_ownership: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PLANNING_LAYER_SPECS: tuple[PlanningLayerSpec, ...] = (
    PlanningLayerSpec(
        kind="future",
        layer="prediction",
        title="Future Completion Brief",
        question="What should be true in the future?",
        timing="before implementation",
        purpose=(
            "Predict the desired completed state before any executor runs. "
            "This layer names the success state, invariants, failure conditions, and non-goals."
        ),
        headings=(
            "Completed State",
            "Invariants To Preserve",
            "Failure Conditions",
            "Non-Goals",
        ),
    ),
    PlanningLayerSpec(
        kind="ontology",
        layer="reality_boundary",
        title="Ontology Brief",
        question="What exists, who owns it, and where are the boundaries?",
        timing="before implementation",
        purpose=(
            "Define the real entities, relationships, owners, approval boundaries, artifact boundaries, "
            "and explicit non-entities that the plan must respect."
        ),
        headings=(
            "Entities",
            "Relationships",
            "Ownership Boundaries",
            "Approval Boundaries",
            "Artifact Boundaries",
            "Explicit Non-Entities",
        ),
    ),
    PlanningLayerSpec(
        kind="product",
        layer="post_implementation_acceptance",
        title="Product Brief",
        question="What must be true after implementation for users and operators?",
        timing="define before implementation; verify after implementation",
        purpose=(
            "Translate the future prediction and ontology boundary into user-facing and operator-facing "
            "acceptance criteria that can be checked after implementation."
        ),
        headings=(
            "Customer / User Problem",
            "MVP Scope",
            "Post-Implementation Acceptance Criteria",
            "Operator Evidence To Review",
            "Out Of Scope",
        ),
    ),
)


PLANNING_LAYER_BY_KIND: dict[str, PlanningLayerSpec] = {
    spec.kind: spec for spec in PLANNING_LAYER_SPECS
}


BRIEF_SCHEMA_CONTRACT = BriefSchemaContract(
    schema_version="patchrail.brief_schema.v1",
    owns_canonical_state=False,
    required_kinds=["future", "ontology", "product"],
    sequence=["future", "ontology", "product"],
    record_fields=[
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
    ],
)


HARNESS_CONTRACT = HarnessContract(
    schema_version="patchrail.harness_contract.v1",
    layer="post_implementation_evidence",
    phase="after_executor_run_before_review",
    owns_canonical_state=False,
    captures=[
        "execution_summary",
        "diff_summary",
        "stdout",
        "stderr",
        "invocation",
        "runner_trace",
        "artifact_bundle",
    ],
)


EVIDENCE_BUNDLE_CONTRACT = EvidenceBundleContract(
    schema_version="patchrail.evidence_bundle.v1",
    owns_canonical_state=False,
    phase="after_executor_run_before_review",
    required_logical_kinds=[
        "execution_summary",
        "diff_summary",
        "runner_stdout",
        "runner_stderr",
        "runner_invocation",
    ],
    optional_logical_kinds=["runner_trace", "runner_artifact"],
)


RUNNER_CONTRACT = RunnerContract(
    schema_version="patchrail.runner_contract.v1",
    owns_canonical_state=False,
    workspace_files={
        "task": "task.json",
        "plan": "plan.json",
        "output": "output.json",
    },
    reserved_environment=[
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
    runner_writable_paths=[
        "output.json",
        "artifacts/",
        "trace.json",
    ],
    forbidden_ownership=[
        "task_lifecycle_state",
        "canonical_plan",
        "review_verdict",
        "approval_decision",
        "approval_ledger",
    ],
)
