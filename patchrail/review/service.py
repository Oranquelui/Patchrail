from __future__ import annotations

from patchrail.core.exceptions import PatchrailError
from patchrail.core.ids import generate_id, utc_now
from patchrail.core.state_machine import require_state, transition_task
from patchrail.models.entities import DecisionTrace, ReviewResult, ReviewVerdict, Run, Task, TaskState
from patchrail.models.roles import FallbackEvent, PreflightResult, ResolvedAssignment
from patchrail.storage.filesystem import FilesystemStore


class ReviewService:
    def __init__(self, store: FilesystemStore) -> None:
        self.store = store

    def create_review(
        self,
        task: Task,
        run: Run,
        verdict: ReviewVerdict,
        summary: str,
        resolved_assignment: ResolvedAssignment | None = None,
        preflight_results: list[PreflightResult] | None = None,
        fallback_event: FallbackEvent | None = None,
    ) -> ReviewResult:
        require_state(task, TaskState.REVIEW_PENDING, "review a run")
        if task.latest_review_id is not None:
            raise PatchrailError(f"Task {task.id} already has a review.")

        review = ReviewResult(
            id=generate_id("review"),
            task_id=task.id,
            run_id=run.id,
            verdict=verdict,
            summary=summary,
            rationale=summary,
            created_at=utc_now(),
            resolved_assignment=resolved_assignment,
            preflight_results=preflight_results or [],
            fallback_event=fallback_event,
        )
        self.store.save_review(review)

        transition_task(task, TaskState.AWAITING_APPROVAL)
        task.latest_review_id = review.id
        task.updated_at = utc_now()
        self.store.save_task(task)
        self.store.append_decision_trace(
            DecisionTrace(
                id=generate_id("trace"),
                task_id=task.id,
                event="review.recorded",
                summary=f"Recorded review {review.id} for run {run.id}.",
                rationale=summary,
                created_at=utc_now(),
                metadata={"run_id": run.id, "verdict": verdict.value},
            )
        )
        return review
