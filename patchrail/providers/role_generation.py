from __future__ import annotations

from patchrail.models.entities import ArtifactBundle, Plan, ReviewVerdict, Run, Task
from patchrail.models.roles import RoleCandidate
from patchrail.workflows.local import LocalWorkflowEngine

_LOCAL_WORKFLOW = LocalWorkflowEngine()


def generate_plan_content(candidate: RoleCandidate, task: Task) -> tuple[str, list[str]]:
    result = _LOCAL_WORKFLOW.generate_plan(candidate, task)
    return result.summary, result.steps


def generate_review_content(
    candidate: RoleCandidate,
    task: Task,
    plan: Plan,
    run: Run,
    bundle: ArtifactBundle,
) -> tuple[ReviewVerdict, str]:
    result = _LOCAL_WORKFLOW.generate_review(candidate, task, plan, run, bundle)
    return result.verdict, result.summary
