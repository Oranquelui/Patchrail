from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import ArtifactBundle, Plan, Run, Task
from patchrail.models.roles import RoleCandidate
from patchrail.workflows.base import PlanWorkflowResult, ReviewWorkflowResult, WorkflowEngine
from patchrail.workflows.local import LocalWorkflowEngine

_GRAPH_VERSION = "mvp.v1"
_CHECKPOINTER_MODE = "stateless"


class _PlanState(TypedDict):
    candidate: RoleCandidate
    task: Task
    metadata: dict[str, Any]
    node_trace: list[str]
    generated_result: PlanWorkflowResult | None
    result: PlanWorkflowResult | None


class _ReviewState(TypedDict):
    candidate: RoleCandidate
    task: Task
    plan: Plan
    run: Run
    bundle: ArtifactBundle
    metadata: dict[str, Any]
    node_trace: list[str]
    generated_result: ReviewWorkflowResult | None
    result: ReviewWorkflowResult | None


class LangGraphWorkflowEngine(WorkflowEngine):
    backend_name = "langgraph"

    def __init__(self) -> None:
        self._local = LocalWorkflowEngine()
        self._plan_graph = self._build_plan_graph()
        self._review_graph = self._build_review_graph()

    def generate_plan(self, candidate: RoleCandidate, task: Task) -> PlanWorkflowResult:
        state = self._plan_graph.invoke(
            {
                "candidate": candidate,
                "task": task,
                "metadata": {},
                "node_trace": [],
                "generated_result": None,
                "result": None,
            }
        )
        result = state.get("result")
        if result is None:
            raise PatchrailError("LangGraph planner workflow did not produce a plan result.")
        return result

    def generate_review(
        self,
        candidate: RoleCandidate,
        task: Task,
        plan: Plan,
        run: Run,
        bundle: ArtifactBundle,
    ) -> ReviewWorkflowResult:
        state = self._review_graph.invoke(
            {
                "candidate": candidate,
                "task": task,
                "plan": plan,
                "run": run,
                "bundle": bundle,
                "metadata": {},
                "node_trace": [],
                "generated_result": None,
                "result": None,
            }
        )
        result = state.get("result")
        if result is None:
            raise PatchrailError("LangGraph reviewer workflow did not produce a review result.")
        return result

    def _build_plan_graph(self):  # noqa: ANN202
        workflow = StateGraph(_PlanState)
        workflow.add_node("collect_plan_context", self._collect_plan_context)
        workflow.add_node("generate_plan", self._generate_plan)
        workflow.add_node("validate_plan", self._validate_plan)
        workflow.add_node("finalize_plan", self._finalize_plan)
        workflow.add_edge(START, "collect_plan_context")
        workflow.add_edge("collect_plan_context", "generate_plan")
        workflow.add_edge("generate_plan", "validate_plan")
        workflow.add_edge("validate_plan", "finalize_plan")
        workflow.add_edge("finalize_plan", END)
        return workflow.compile(checkpointer=False)

    def _build_review_graph(self):  # noqa: ANN202
        workflow = StateGraph(_ReviewState)
        workflow.add_node("collect_review_context", self._collect_review_context)
        workflow.add_node("generate_review", self._generate_review)
        workflow.add_node("validate_review", self._validate_review)
        workflow.add_node("finalize_review", self._finalize_review)
        workflow.add_edge(START, "collect_review_context")
        workflow.add_edge("collect_review_context", "generate_review")
        workflow.add_edge("generate_review", "validate_review")
        workflow.add_edge("validate_review", "finalize_review")
        workflow.add_edge("finalize_review", END)
        return workflow.compile(checkpointer=False)

    def _collect_plan_context(self, state: _PlanState) -> dict[str, object]:
        return {
            "metadata": {
                "graph": "planner",
                "graph_version": _GRAPH_VERSION,
                "checkpointer": _CHECKPOINTER_MODE,
                "delegate_backend": self._local.backend_name,
                "candidate_name": state["candidate"].name,
                "provider": state["candidate"].provider.value,
                "task_id": state["task"].id,
            },
            "node_trace": self._append_trace(state["node_trace"], "collect_plan_context"),
        }

    def _generate_plan(self, state: _PlanState) -> dict[str, object]:
        generated = self._local.generate_plan(state["candidate"], state["task"])
        return {
            "generated_result": generated,
            "metadata": {**state["metadata"], **generated.metadata},
            "node_trace": self._append_trace(state["node_trace"], "generate_plan"),
        }

    def _validate_plan(self, state: _PlanState) -> dict[str, object]:
        generated = state["generated_result"]
        if generated is None or not generated.summary or not generated.steps:
            raise PatchrailError("LangGraph planner workflow produced an invalid plan result.")
        return {"node_trace": self._append_trace(state["node_trace"], "validate_plan")}

    def _finalize_plan(self, state: _PlanState) -> dict[str, object]:
        generated = state["generated_result"]
        if generated is None:
            raise PatchrailError("LangGraph planner workflow had no generated plan to finalize.")
        node_trace = self._append_trace(state["node_trace"], "finalize_plan")
        return {
            "node_trace": node_trace,
            "result": PlanWorkflowResult(
                summary=generated.summary,
                steps=generated.steps,
                metadata={**state["metadata"], "node_trace": node_trace},
            ),
        }

    def _collect_review_context(self, state: _ReviewState) -> dict[str, object]:
        return {
            "metadata": {
                "graph": "reviewer",
                "graph_version": _GRAPH_VERSION,
                "checkpointer": _CHECKPOINTER_MODE,
                "delegate_backend": self._local.backend_name,
                "candidate_name": state["candidate"].name,
                "provider": state["candidate"].provider.value,
                "task_id": state["task"].id,
                "run_id": state["run"].id,
                "artifact_bundle_id": state["bundle"].run_id,
            },
            "node_trace": self._append_trace(state["node_trace"], "collect_review_context"),
        }

    def _generate_review(self, state: _ReviewState) -> dict[str, object]:
        generated = self._local.generate_review(
            state["candidate"],
            state["task"],
            state["plan"],
            state["run"],
            state["bundle"],
        )
        return {
            "generated_result": generated,
            "metadata": {**state["metadata"], **generated.metadata},
            "node_trace": self._append_trace(state["node_trace"], "generate_review"),
        }

    def _validate_review(self, state: _ReviewState) -> dict[str, object]:
        generated = state["generated_result"]
        if generated is None or not generated.summary:
            raise PatchrailError("LangGraph reviewer workflow produced an invalid review result.")
        return {"node_trace": self._append_trace(state["node_trace"], "validate_review")}

    def _finalize_review(self, state: _ReviewState) -> dict[str, object]:
        generated = state["generated_result"]
        if generated is None:
            raise PatchrailError("LangGraph reviewer workflow had no generated review to finalize.")
        node_trace = self._append_trace(state["node_trace"], "finalize_review")
        return {
            "node_trace": node_trace,
            "result": ReviewWorkflowResult(
                verdict=generated.verdict,
                summary=generated.summary,
                metadata={**state["metadata"], "node_trace": node_trace},
            ),
        }

    @staticmethod
    def _append_trace(existing: list[str], node_name: str) -> list[str]:
        return [*existing, node_name]
