from __future__ import annotations

from patchrail.core.exceptions import PatchrailError
from patchrail.core.ids import generate_id, utc_now
from patchrail.core.state_machine import require_state, transition_task
from patchrail.models.entities import (
    ApprovalDecision,
    ApprovalRecord,
    DecisionTrace,
    ReviewResult,
    Task,
    TaskState,
)
from patchrail.storage.filesystem import FilesystemStore


class ApprovalService:
    def __init__(self, store: FilesystemStore) -> None:
        self.store = store

    def record_decision(self, task: Task, review: ReviewResult, decision: ApprovalDecision, rationale: str) -> ApprovalRecord:
        require_state(task, TaskState.AWAITING_APPROVAL, "record an approval decision")
        if task.latest_review_id != review.id:
            raise PatchrailError(f"Task {task.id} does not point at review {review.id}.")

        approval = ApprovalRecord(
            id=generate_id("approval"),
            task_id=task.id,
            review_id=review.id,
            decision=decision,
            rationale=rationale,
            actor="human",
            created_at=utc_now(),
        )
        self.store.save_approval(approval)
        self.store.append_approval_ledger(approval)

        transition_task(task, TaskState(decision.value))
        task.latest_approval_id = approval.id
        task.updated_at = utc_now()
        self.store.save_task(task)
        self.store.append_decision_trace(
            DecisionTrace(
                id=generate_id("trace"),
                task_id=task.id,
                event=f"task.{decision.value}",
                summary=f"Task {task.id} marked as {decision.value}.",
                rationale=rationale,
                created_at=utc_now(),
                metadata={"review_id": review.id, "approval_id": approval.id},
            )
        )
        return approval
