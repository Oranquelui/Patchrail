from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from patchrail.models.roles import FallbackEvent, PreflightResult, ResolvedAssignment


class TaskState(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    RUNNING = "running"
    REVIEW_PENDING = "review_pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class PlanStatus(StrEnum):
    READY = "ready"


class RunStatus(StrEnum):
    COMPLETED = "completed"


class ReviewVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class ApprovalDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class FallbackApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PreflightPhase(StrEnum):
    PLAN = "plan"
    RUN = "run"
    REVIEW = "review"


@dataclass(slots=True)
class CostMetrics:
    prompt_tokens: int
    completion_tokens: int
    estimated_usd: float
    elapsed_seconds: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CostMetrics:
        return cls(**payload)


@dataclass(slots=True)
class RunnerAssignment:
    runner_name: str
    mode: str
    command: str | None
    assigned_by: str
    assigned_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RunnerAssignment:
        return cls(**payload)


@dataclass(slots=True)
class Task:
    id: str
    title: str
    description: str
    state: TaskState
    created_at: str
    updated_at: str
    plan_id: str | None = None
    latest_run_id: str | None = None
    latest_review_id: str | None = None
    latest_approval_id: str | None = None
    latest_fallback_request_id: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Task:
        return cls(
            id=payload["id"],
            title=payload["title"],
            description=payload["description"],
            state=TaskState(payload["state"]),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            plan_id=payload.get("plan_id"),
            latest_run_id=payload.get("latest_run_id"),
            latest_review_id=payload.get("latest_review_id"),
            latest_approval_id=payload.get("latest_approval_id"),
            latest_fallback_request_id=payload.get("latest_fallback_request_id"),
        )


@dataclass(slots=True)
class Plan:
    id: str
    task_id: str
    summary: str
    steps: list[str]
    status: PlanStatus
    created_at: str
    resolved_assignment: ResolvedAssignment | None = None
    preflight_results: list[PreflightResult] = field(default_factory=list)
    fallback_event: FallbackEvent | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Plan:
        return cls(
            id=payload["id"],
            task_id=payload["task_id"],
            summary=payload["summary"],
            steps=list(payload["steps"]),
            status=PlanStatus(payload["status"]),
            created_at=payload["created_at"],
            resolved_assignment=ResolvedAssignment.from_dict(payload["resolved_assignment"])
            if payload.get("resolved_assignment")
            else None,
            preflight_results=[PreflightResult.from_dict(item) for item in payload.get("preflight_results", [])],
            fallback_event=FallbackEvent.from_dict(payload["fallback_event"]) if payload.get("fallback_event") else None,
        )


@dataclass(slots=True)
class ArtifactBundle:
    run_id: str
    created_at: str
    files: dict[str, str]
    summary: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ArtifactBundle:
        return cls(
            run_id=payload["run_id"],
            created_at=payload["created_at"],
            files=dict(payload["files"]),
            summary=payload["summary"],
        )


@dataclass(slots=True)
class Run:
    id: str
    task_id: str
    plan_id: str
    runner_assignment: RunnerAssignment
    status: RunStatus
    created_at: str
    completed_at: str
    cost_metrics: CostMetrics
    artifact_bundle_id: str
    workspace_path: str
    exit_code: int
    summary: str
    resolved_assignment: ResolvedAssignment | None = None
    preflight_results: list[PreflightResult] = field(default_factory=list)
    fallback_event: FallbackEvent | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Run:
        return cls(
            id=payload["id"],
            task_id=payload["task_id"],
            plan_id=payload["plan_id"],
            runner_assignment=RunnerAssignment.from_dict(payload["runner_assignment"]),
            status=RunStatus(payload["status"]),
            created_at=payload["created_at"],
            completed_at=payload["completed_at"],
            cost_metrics=CostMetrics.from_dict(payload["cost_metrics"]),
            artifact_bundle_id=payload["artifact_bundle_id"],
            workspace_path=payload["workspace_path"],
            exit_code=payload["exit_code"],
            summary=payload["summary"],
            resolved_assignment=ResolvedAssignment.from_dict(payload["resolved_assignment"])
            if payload.get("resolved_assignment")
            else None,
            preflight_results=[PreflightResult.from_dict(item) for item in payload.get("preflight_results", [])],
            fallback_event=FallbackEvent.from_dict(payload["fallback_event"]) if payload.get("fallback_event") else None,
        )


@dataclass(slots=True)
class ReviewResult:
    id: str
    task_id: str
    run_id: str
    verdict: ReviewVerdict
    summary: str
    rationale: str
    created_at: str
    resolved_assignment: ResolvedAssignment | None = None
    preflight_results: list[PreflightResult] = field(default_factory=list)
    fallback_event: FallbackEvent | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReviewResult:
        return cls(
            id=payload["id"],
            task_id=payload["task_id"],
            run_id=payload["run_id"],
            verdict=ReviewVerdict(payload["verdict"]),
            summary=payload["summary"],
            rationale=payload["rationale"],
            created_at=payload["created_at"],
            resolved_assignment=ResolvedAssignment.from_dict(payload["resolved_assignment"])
            if payload.get("resolved_assignment")
            else None,
            preflight_results=[PreflightResult.from_dict(item) for item in payload.get("preflight_results", [])],
            fallback_event=FallbackEvent.from_dict(payload["fallback_event"]) if payload.get("fallback_event") else None,
        )


@dataclass(slots=True)
class ApprovalRecord:
    id: str
    task_id: str
    review_id: str
    decision: ApprovalDecision
    rationale: str
    actor: str
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ApprovalRecord:
        return cls(
            id=payload["id"],
            task_id=payload["task_id"],
            review_id=payload["review_id"],
            decision=ApprovalDecision(payload["decision"]),
            rationale=payload["rationale"],
            actor=payload["actor"],
            created_at=payload["created_at"],
        )


@dataclass(slots=True)
class FallbackApprovalRequest:
    id: str
    task_id: str
    role: str
    requested_assignment: ResolvedAssignment
    fallback_event: FallbackEvent
    preflight_results: list[PreflightResult]
    status: FallbackApprovalStatus
    created_at: str
    decided_at: str | None = None
    rationale: str | None = None
    actor: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FallbackApprovalRequest:
        return cls(
            id=payload["id"],
            task_id=payload["task_id"],
            role=payload["role"],
            requested_assignment=ResolvedAssignment.from_dict(payload["requested_assignment"]),
            fallback_event=FallbackEvent.from_dict(payload["fallback_event"]),
            preflight_results=[PreflightResult.from_dict(item) for item in payload.get("preflight_results", [])],
            status=FallbackApprovalStatus(payload["status"]),
            created_at=payload["created_at"],
            decided_at=payload.get("decided_at"),
            rationale=payload.get("rationale"),
            actor=payload.get("actor"),
        )


@dataclass(slots=True)
class PreflightSnapshot:
    id: str
    task_id: str
    phase: PreflightPhase
    role: str
    selected_assignment: ResolvedAssignment | None
    preflight_results: list[PreflightResult]
    fallback_event: FallbackEvent | None
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PreflightSnapshot:
        return cls(
            id=payload["id"],
            task_id=payload["task_id"],
            phase=PreflightPhase(payload["phase"]),
            role=payload["role"],
            selected_assignment=ResolvedAssignment.from_dict(payload["selected_assignment"])
            if payload.get("selected_assignment")
            else None,
            preflight_results=[PreflightResult.from_dict(item) for item in payload.get("preflight_results", [])],
            fallback_event=FallbackEvent.from_dict(payload["fallback_event"]) if payload.get("fallback_event") else None,
            created_at=payload["created_at"],
        )


@dataclass(slots=True)
class DecisionTrace:
    id: str
    task_id: str
    event: str
    summary: str
    rationale: str | None
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DecisionTrace:
        return cls(
            id=payload["id"],
            task_id=payload["task_id"],
            event=payload["event"],
            summary=payload["summary"],
            rationale=payload.get("rationale"),
            created_at=payload["created_at"],
            metadata=dict(payload.get("metadata", {})),
        )


def serialize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return serialize(asdict(value))
    return value
