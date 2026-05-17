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
