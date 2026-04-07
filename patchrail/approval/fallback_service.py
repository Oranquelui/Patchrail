from __future__ import annotations

from patchrail.core.exceptions import PatchrailError
from patchrail.core.ids import generate_id, utc_now
from patchrail.models.entities import (
    DecisionTrace,
    FallbackApprovalRequest,
    FallbackApprovalStatus,
    Task,
)
from patchrail.models.roles import FallbackEvent, PreflightResult, ResolvedAssignment, Role
from patchrail.storage.filesystem import FilesystemStore


class FallbackApprovalService:
    def __init__(self, store: FilesystemStore) -> None:
        self.store = store

    def create_request(
        self,
        task: Task,
        role: Role,
        assignment: ResolvedAssignment,
        preflight_results: list[PreflightResult],
        fallback_event: FallbackEvent,
    ) -> FallbackApprovalRequest:
        request = FallbackApprovalRequest(
            id=generate_id("fallback"),
            task_id=task.id,
            role=role.value,
            requested_assignment=assignment,
            fallback_event=fallback_event,
            preflight_results=preflight_results,
            status=FallbackApprovalStatus.PENDING,
            created_at=utc_now(),
        )
        self.store.save_fallback_request(request)
        self.store.append_fallback_approval_ledger(request)

        task.latest_fallback_request_id = request.id
        task.updated_at = utc_now()
        self.store.save_task(task)
        self.store.append_decision_trace(
            DecisionTrace(
                id=generate_id("trace"),
                task_id=task.id,
                event=f"{role.value}.fallback_requested",
                summary=f"Fallback request {request.id} created for role {role.value}.",
                rationale=None,
                created_at=utc_now(),
                metadata={
                    "fallback_request_id": request.id,
                    "requested_assignment": assignment,
                    "fallback_event": fallback_event,
                },
            )
        )
        return request

    def record_decision(
        self,
        task: Task,
        decision: FallbackApprovalStatus,
        rationale: str,
    ) -> FallbackApprovalRequest:
        if task.latest_fallback_request_id is None:
            raise PatchrailError(f"Task {task.id} has no fallback approval request.")
        request = self.store.load_fallback_request(task.latest_fallback_request_id)
        if request.status != FallbackApprovalStatus.PENDING:
            raise PatchrailError(
                f"Fallback request {request.id} is already {request.status.value}."
            )

        request.status = decision
        request.decided_at = utc_now()
        request.rationale = rationale
        request.actor = "human"
        self.store.save_fallback_request(request)
        self.store.append_fallback_approval_ledger(request)
        task.updated_at = utc_now()
        self.store.save_task(task)
        self.store.append_decision_trace(
            DecisionTrace(
                id=generate_id("trace"),
                task_id=task.id,
                event=f"{request.role}.fallback_{decision.value}",
                summary=f"Fallback request {request.id} marked as {decision.value}.",
                rationale=rationale,
                created_at=utc_now(),
                metadata={"fallback_request_id": request.id},
            )
        )
        return request
