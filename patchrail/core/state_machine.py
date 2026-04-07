from __future__ import annotations

from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import Task, TaskState


ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.CREATED: {TaskState.PLANNED},
    TaskState.PLANNED: {TaskState.RUNNING},
    TaskState.RUNNING: {TaskState.REVIEW_PENDING},
    TaskState.REVIEW_PENDING: {TaskState.AWAITING_APPROVAL},
    TaskState.AWAITING_APPROVAL: {TaskState.APPROVED, TaskState.REJECTED},
    TaskState.APPROVED: set(),
    TaskState.REJECTED: set(),
}


def require_state(task: Task, expected: TaskState, action: str) -> None:
    if task.state != expected:
        raise PatchrailError(
            f"Task {task.id} must be in state '{expected.value}' to {action}; found '{task.state.value}'."
        )


def transition_task(task: Task, next_state: TaskState) -> None:
    if next_state not in ALLOWED_TRANSITIONS[task.state]:
        raise PatchrailError(f"Cannot transition task {task.id} from '{task.state.value}' to '{next_state.value}'.")
    task.state = next_state
