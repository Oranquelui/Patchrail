from __future__ import annotations

from typing import TypedDict

from patchrail.models.entities import ArtifactBundle, Plan, Run, Task
from patchrail.models.roles import RoleCandidate
from patchrail.workflows.base import PlanWorkflowResult, ReviewWorkflowResult, WorkflowEngine
from patchrail.workflows.local import LocalWorkflowEngine

from langgraph.graph import END, START, StateGraph


class _PlanState(TypedDict):
    candidate: RoleCandidate
    task: Task
    result: PlanWorkflowResult | None


class _ReviewState(TypedDict):
    candidate: RoleCandidate
    task: Task
    plan: Plan
    run: Run
    bundle: ArtifactBundle
    result: ReviewWorkflowResult | None


class LangGraphWorkflowEngine(WorkflowEngine):
    backend_name = "langgraph"

    def __init__(self) -> None:
        self._local = LocalWorkflowEngine()

    def generate_plan(self, candidate: RoleCandidate, task: Task) -> PlanWorkflowResult:
        workflow = StateGraph(_PlanState)
        workflow.add_node("generate_plan", self._plan_node)
        workflow.add_edge(START, "generate_plan")
        workflow.add_edge("generate_plan", END)
        compiled = workflow.compile()
        result = compiled.invoke({"candidate": candidate, "task": task, "result": None})["result"]
        return PlanWorkflowResult(
            summary=result.summary,
            steps=result.steps,
            metadata={**result.metadata, "graph": "planner", "delegate_backend": self._local.backend_name},
        )

    def generate_review(
        self,
        candidate: RoleCandidate,
        task: Task,
        plan: Plan,
        run: Run,
        bundle: ArtifactBundle,
    ) -> ReviewWorkflowResult:
        workflow = StateGraph(_ReviewState)
        workflow.add_node("generate_review", self._review_node)
        workflow.add_edge(START, "generate_review")
        workflow.add_edge("generate_review", END)
        compiled = workflow.compile()
        result = compiled.invoke(
            {"candidate": candidate, "task": task, "plan": plan, "run": run, "bundle": bundle, "result": None}
        )["result"]
        return ReviewWorkflowResult(
            verdict=result.verdict,
            summary=result.summary,
            metadata={**result.metadata, "graph": "reviewer", "delegate_backend": self._local.backend_name},
        )

    def _plan_node(self, state: _PlanState) -> dict[str, PlanWorkflowResult]:
        return {"result": self._local.generate_plan(state["candidate"], state["task"])}

    def _review_node(self, state: _ReviewState) -> dict[str, ReviewWorkflowResult]:
        return {
            "result": self._local.generate_review(
                state["candidate"],
                state["task"],
                state["plan"],
                state["run"],
                state["bundle"],
            )
        }
