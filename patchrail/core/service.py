from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from patchrail.approval.service import ApprovalService
from patchrail.approval.fallback_service import FallbackApprovalService
from patchrail.core.assignment import resolve_role_assignment
from patchrail.artifacts.service import ArtifactService
from patchrail.core.exceptions import PatchrailError
from patchrail.core.hooks import HookEvent, HookRegistry
from patchrail.core.ids import generate_id, utc_now
from patchrail.core.state_machine import require_state, transition_task
from patchrail.models.entities import (
    ApprovalDecision,
    DecisionTrace,
    FallbackApprovalStatus,
    Plan,
    PlanStatus,
    PreflightPhase,
    PreflightSnapshot,
    ReviewVerdict,
    Run,
    RunnerAssignment,
    RunStatus,
    Task,
    TaskState,
    serialize,
)
from patchrail.models.roles import AccessMode, Provider, Role
from patchrail.review.service import ReviewService
from patchrail.runners.api import build_api_runner
from patchrail.runners.subscription import build_subscription_runner
from patchrail.runners.stub import build_runner
from patchrail.storage.config_store import ConfigStore
from patchrail.storage.filesystem import FilesystemStore
from patchrail.workflows import WorkflowEngine, build_workflow_engine


class PatchrailApp:
    def __init__(self, store: FilesystemStore) -> None:
        self.store = store
        self.config = ConfigStore(store.root)
        self.hooks = HookRegistry()
        self.artifacts = ArtifactService(store)
        self.review = ReviewService(store)
        self.approval = ApprovalService(store)
        self.fallback_approval = FallbackApprovalService(store)
        self._workflow_engine_instance: WorkflowEngine | None = None

    @classmethod
    def from_environment(cls, cwd: Path | None = None) -> PatchrailApp:
        return cls(FilesystemStore.from_environment(cwd=cwd))

    def create_task(self, title: str, description: str) -> dict[str, Any]:
        timestamp = utc_now()
        task = Task(
            id=generate_id("task"),
            title=title,
            description=description,
            state=TaskState.CREATED,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.save_task(task)
        self._append_trace(task.id, "task.created", f"Created task {task.id}.", description)
        return {"task": serialize(task)}

    def init_config(self, preset: str = "local", workflow_backend: str = "local") -> dict[str, Any]:
        policy = self.config.init_default(preset=preset, workflow_backend=workflow_backend)
        self._workflow_engine_instance = None
        return {
            "config": {"path": str(self.config.config_path), "preset": preset, "roles": serialize(policy)},
            "workflow": {"path": str(self.config.workflow_path), "backend": self.config.load_workflow_backend()},
        }

    def preflight(
        self,
        role_name: str,
        runner_name: str | None = None,
        access_mode_name: str = "auto",
    ) -> dict[str, Any]:
        role = Role(role_name)
        provider_filter = self._provider_filter_for_role(role=role, runner_name=runner_name)
        resolution = resolve_role_assignment(
            self.config.load_policy(),
            role=role,
            provider_filter=provider_filter,
            access_mode_filter=self._access_mode_filter(access_mode_name),
        )
        return {
            "role": role.value,
            "selected_candidate": serialize(resolution.selected_assignment) if resolution.selected_assignment else None,
            "results": serialize(resolution.results),
            "fallback_event": serialize(resolution.fallback_event) if resolution.fallback_event else None,
        }

    def create_plan(
        self,
        task_id: str,
        summary: str | None,
        steps: list[str] | None,
        auto: bool = False,
        access_mode_name: str = "auto",
    ) -> dict[str, Any]:
        task = self.store.load_task(task_id)
        require_state(task, TaskState.CREATED, "create a plan")
        self._validate_plan_inputs(auto=auto, summary=summary, steps=steps)
        resolution = resolve_role_assignment(
            self.config.load_policy(),
            role=Role.PLANNER,
            access_mode_filter=self._access_mode_filter(access_mode_name) if auto else None,
        )
        self._record_preflight_snapshot(task.id, phase=PreflightPhase.PLAN, role=Role.PLANNER, resolution=resolution)
        assignment = self._require_assignment(task, role=Role.PLANNER, resolution=resolution)
        workflow_result = None
        if auto:
            if resolution.selected_candidate is None:
                raise PatchrailError("No planner candidate was selected.")
            workflow_result = self._get_workflow_engine().generate_plan(resolution.selected_candidate, task)
            summary, steps = workflow_result.summary, workflow_result.steps
            self._append_trace(
                task.id,
                "plan.generated",
                f"Generated plan content via {assignment.candidate_name} using {self._get_workflow_engine().backend_name}.",
                metadata={
                    "assignment": serialize(assignment),
                    "workflow_backend": self._get_workflow_engine().backend_name,
                    "workflow_metadata": serialize(workflow_result.metadata),
                },
            )
        if summary is None or steps is None:
            raise PatchrailError("Plan requires summary and at least one step.")

        plan = Plan(
            id=generate_id("plan"),
            task_id=task.id,
            summary=summary,
            steps=steps,
            status=PlanStatus.READY,
            created_at=utc_now(),
            resolved_assignment=assignment,
            preflight_results=resolution.results,
            fallback_event=resolution.fallback_event,
            workflow_backend=self._get_workflow_engine().backend_name if workflow_result else None,
            workflow_metadata=workflow_result.metadata if workflow_result else {},
        )
        self.store.save_plan(plan)
        task.plan_id = plan.id
        transition_task(task, TaskState.PLANNED)
        task.updated_at = utc_now()
        self.store.save_task(task)
        self._append_trace(task.id, "plan.created", f"Stored plan {plan.id} for task {task.id}.", summary)
        self._append_trace(
            task.id,
            "planner.resolved",
            f"Resolved planner candidate {assignment.candidate_name} for task {task.id}.",
            metadata={
                "assignment": serialize(assignment),
                "preflight_results": serialize(resolution.results),
                "fallback_event": serialize(resolution.fallback_event) if resolution.fallback_event else None,
            },
        )
        return {"plan": serialize(plan), "task": serialize(task)}

    def run_task(self, task_id: str, runner_name: str, access_mode_name: str = "auto") -> dict[str, Any]:
        task = self.store.load_task(task_id)
        require_state(task, TaskState.PLANNED, "run a task")
        if task.plan_id is None:
            raise PatchrailError(f"Task {task.id} has no plan and cannot run.")

        plan = self.store.load_plan(task.plan_id)
        resolution = resolve_role_assignment(
            self.config.load_policy(),
            role=Role.EXECUTOR,
            provider_filter=self._provider_filter_for_role(role=Role.EXECUTOR, runner_name=runner_name),
            access_mode_filter=self._access_mode_filter(access_mode_name),
        )
        self._record_preflight_snapshot(task.id, phase=PreflightPhase.RUN, role=Role.EXECUTOR, resolution=resolution)
        assignment_selection = self._require_assignment(task, role=Role.EXECUTOR, resolution=resolution)
        run_id = generate_id("run")
        workspace_path = self._prepare_workspace(run_id=run_id, task=task, plan=plan)
        if (
            resolution.selected_candidate
            and resolution.selected_candidate.access_mode == AccessMode.API
            and not resolution.selected_candidate.simulation
        ):
            runner = build_api_runner(resolution.selected_candidate, runner_name)
        elif (
            resolution.selected_candidate
            and resolution.selected_candidate.access_mode == AccessMode.SUBSCRIPTION
            and not resolution.selected_candidate.simulation
            and resolution.selected_candidate.provider == Provider.CLAUDE
        ):
            runner = build_subscription_runner(resolution.selected_candidate, runner_name)
        else:
            runner = build_runner(runner_name, command=assignment_selection.command)
        assignment = RunnerAssignment(
            runner_name=runner_name,
            mode=runner.mode,
            command=runner.command,
            assigned_by="codex",
            assigned_at=utc_now(),
        )
        result = runner.run(task, plan, workspace_path=workspace_path, run_id=run_id)

        transition_task(task, TaskState.RUNNING)
        task.updated_at = utc_now()
        self.store.save_task(task)
        self._append_trace(
            task.id,
            "run.started",
            f"Started runner {runner_name} for task {task.id}.",
            metadata={"runner": runner_name, "run_id": run_id, "mode": runner.mode},
        )

        invocation = {
            "runner": runner_name,
            "mode": runner.mode,
            "command": runner.command,
            "workspace_path": str(workspace_path),
            "task_file": str(workspace_path / "task.json"),
            "plan_file": str(workspace_path / "plan.json"),
            "output_file": str(workspace_path / "output.json"),
            "exit_code": result.exit_code,
        }
        bundle = self.artifacts.create_bundle(
            run_id=run_id,
            execution_summary=result.execution_summary,
            diff_summary=result.diff_summary,
            stdout=result.stdout,
            stderr=result.stderr,
            invocation=invocation,
        )
        run = Run(
            id=run_id,
            task_id=task.id,
            plan_id=plan.id,
            runner_assignment=assignment,
            status=RunStatus.COMPLETED,
            created_at=assignment.assigned_at,
            completed_at=utc_now(),
            cost_metrics=result.cost_metrics,
            artifact_bundle_id=bundle.run_id,
            workspace_path=str(workspace_path),
            exit_code=result.exit_code,
            summary=result.execution_summary,
            resolved_assignment=assignment_selection,
            preflight_results=resolution.results,
            fallback_event=resolution.fallback_event,
        )
        self.store.save_run(run)

        transition_task(task, TaskState.REVIEW_PENDING)
        task.latest_run_id = run.id
        task.updated_at = utc_now()
        self.store.save_task(task)
        self._append_trace(
            task.id,
            "run.completed",
            f"Completed run {run.id} for task {task.id}.",
            metadata={"run_id": run.id, "runner": runner_name},
        )
        self._append_trace(
            task.id,
            "executor.resolved",
            f"Resolved executor candidate {assignment_selection.candidate_name} for task {task.id}.",
            metadata={
                "assignment": serialize(assignment_selection),
                "preflight_results": serialize(resolution.results),
                "fallback_event": serialize(resolution.fallback_event) if resolution.fallback_event else None,
            },
        )
        self.hooks.dispatch(HookEvent(name="run.completed", payload={"task_id": task.id, "run_id": run.id}))
        return {"run": serialize(run), "task": serialize(task), "artifact_bundle": serialize(bundle)}

    def review_run(
        self,
        run_id: str,
        verdict: str | None,
        summary: str | None,
        auto: bool = False,
        access_mode_name: str = "auto",
    ) -> dict[str, Any]:
        run = self.store.load_run(run_id)
        task = self.store.load_task(run.task_id)
        if task.latest_run_id != run.id:
            raise PatchrailError(f"Run {run.id} is not the latest run for task {task.id}.")
        self._validate_review_inputs(auto=auto, verdict=verdict, summary=summary)
        resolution = resolve_role_assignment(
            self.config.load_policy(),
            role=Role.REVIEWER,
            access_mode_filter=self._access_mode_filter(access_mode_name) if auto else None,
        )
        self._record_preflight_snapshot(task.id, phase=PreflightPhase.REVIEW, role=Role.REVIEWER, resolution=resolution)
        assignment = self._require_assignment(task, role=Role.REVIEWER, resolution=resolution)
        workflow_result = None
        if auto:
            if task.plan_id is None:
                raise PatchrailError(f"Task {task.id} has no plan for automated review.")
            if resolution.selected_candidate is None:
                raise PatchrailError("No reviewer candidate was selected.")
            plan = self.store.load_plan(task.plan_id)
            bundle = self.store.load_artifact_bundle(run.id)
            workflow_result = self._get_workflow_engine().generate_review(
                resolution.selected_candidate,
                task,
                plan,
                run,
                bundle,
            )
            verdict_value = workflow_result.verdict
            summary_value = workflow_result.summary
            self._append_trace(
                task.id,
                "review.generated",
                f"Generated review content via {assignment.candidate_name} using {self._get_workflow_engine().backend_name}.",
                metadata={
                    "assignment": serialize(assignment),
                    "verdict": verdict_value.value,
                    "workflow_backend": self._get_workflow_engine().backend_name,
                    "workflow_metadata": serialize(workflow_result.metadata),
                },
            )
        else:
            if verdict is None or summary is None:
                raise PatchrailError("Review requires verdict and summary.")
            verdict_value = ReviewVerdict(verdict)
            summary_value = summary

        review = self.review.create_review(
            task,
            run,
            verdict_value,
            summary_value,
            resolved_assignment=assignment,
            preflight_results=resolution.results,
            fallback_event=resolution.fallback_event,
            workflow_backend=self._get_workflow_engine().backend_name if workflow_result else None,
            workflow_metadata=workflow_result.metadata if workflow_result else {},
        )
        self._append_trace(
            task.id,
            "reviewer.resolved",
            f"Resolved reviewer candidate {assignment.candidate_name} for task {task.id}.",
            metadata={
                "assignment": serialize(assignment),
                "preflight_results": serialize(resolution.results),
                "fallback_event": serialize(resolution.fallback_event) if resolution.fallback_event else None,
            },
        )
        return {"review": serialize(review), "task": serialize(task)}

    def approve_task(self, task_id: str, rationale: str) -> dict[str, Any]:
        return self._finalize_task(task_id, ApprovalDecision.APPROVED, rationale)

    def reject_task(self, task_id: str, rationale: str) -> dict[str, Any]:
        return self._finalize_task(task_id, ApprovalDecision.REJECTED, rationale)

    def approve_fallback(self, task_id: str, rationale: str) -> dict[str, Any]:
        return self._finalize_fallback(task_id, FallbackApprovalStatus.APPROVED, rationale)

    def reject_fallback(self, task_id: str, rationale: str) -> dict[str, Any]:
        return self._finalize_fallback(task_id, FallbackApprovalStatus.REJECTED, rationale)

    def _finalize_task(self, task_id: str, decision: ApprovalDecision, rationale: str) -> dict[str, Any]:
        task = self.store.load_task(task_id)
        if task.latest_review_id is None:
            raise PatchrailError(f"Task {task.id} requires a completed review before {decision.value}.")
        review = self.store.load_review(task.latest_review_id)
        approval = self.approval.record_decision(task, review, decision, rationale)
        self.hooks.dispatch(HookEvent(name=f"task.{decision.value}", payload={"task_id": task.id}))
        return {"approval": serialize(approval), "task": serialize(task)}

    def _finalize_fallback(
        self,
        task_id: str,
        decision: FallbackApprovalStatus,
        rationale: str,
    ) -> dict[str, Any]:
        task = self.store.load_task(task_id)
        request = self.fallback_approval.record_decision(task, decision, rationale)
        self.hooks.dispatch(HookEvent(name=f"fallback.{decision.value}", payload={"task_id": task.id}))
        return {"fallback_request": serialize(request), "task": serialize(task)}

    def get_status(self, task_id: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        if task_id:
            task = self.store.load_task(task_id)
        elif run_id:
            run = self.store.load_run(run_id)
            task = self.store.load_task(run.task_id)
        else:
            raise PatchrailError("Provide either --task-id or --run-id.")

        payload: dict[str, Any] = {"task": serialize(task)}
        if task.plan_id:
            payload["plan"] = serialize(self.store.load_plan(task.plan_id))
        if task.latest_run_id:
            payload["latest_run"] = serialize(self.store.load_run(task.latest_run_id))
        if task.latest_review_id:
            payload["latest_review"] = serialize(self.store.load_review(task.latest_review_id))
        if task.latest_approval_id:
            payload["latest_approval"] = serialize(self.store.load_approval(task.latest_approval_id))
        if task.latest_fallback_request_id:
            payload["latest_fallback_request"] = serialize(
                self.store.load_fallback_request(task.latest_fallback_request_id)
            )
        return payload

    def get_logs(self, run_id: str) -> dict[str, Any]:
        self.store.load_run(run_id)
        return {"run_id": run_id, "stdout": self.artifacts.get_stdout(run_id)}

    def get_artifacts(self, run_id: str) -> dict[str, Any]:
        self.store.load_run(run_id)
        return {"artifact_bundle": serialize(self.artifacts.get_bundle(run_id))}

    def list_tasks(self) -> dict[str, Any]:
        return {"tasks": serialize(self.store.list_tasks())}

    def list_runs(self, task_id: str | None = None) -> dict[str, Any]:
        runs = self.store.list_runs()
        if task_id is not None:
            runs = [run for run in runs if run.task_id == task_id]
        return {"runs": serialize(runs)}

    def list_plans(self, task_id: str | None = None) -> dict[str, Any]:
        plans = self.store.list_plans()
        if task_id is not None:
            plans = [plan for plan in plans if plan.task_id == task_id]
        return {"plans": serialize(plans)}

    def list_approvals(self, task_id: str | None = None) -> dict[str, Any]:
        approvals = self.store.list_approvals()
        if task_id is not None:
            approvals = [approval for approval in approvals if approval.task_id == task_id]
        return {"approvals": serialize(approvals)}

    def list_reviews(self, task_id: str | None = None) -> dict[str, Any]:
        reviews = self.store.list_reviews()
        if task_id is not None:
            reviews = [review for review in reviews if review.task_id == task_id]
        return {"reviews": serialize(reviews)}

    def list_fallback_requests(self, task_id: str | None = None) -> dict[str, Any]:
        requests = self.store.list_fallback_requests()
        if task_id is not None:
            requests = [request for request in requests if request.task_id == task_id]
        return {"fallback_requests": serialize(requests)}

    def list_preflight_snapshots(self, task_id: str | None = None) -> dict[str, Any]:
        snapshots = self.store.list_preflight_snapshots()
        if task_id is not None:
            snapshots = [snapshot for snapshot in snapshots if snapshot.task_id == task_id]
        return {"preflight_snapshots": serialize(snapshots)}

    def _append_trace(
        self,
        task_id: str,
        event: str,
        summary: str,
        rationale: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        trace = DecisionTrace(
            id=generate_id("trace"),
            task_id=task_id,
            event=event,
            summary=summary,
            rationale=rationale,
            created_at=utc_now(),
            metadata=metadata or {},
        )
        self.store.append_decision_trace(trace)

    def _prepare_workspace(self, run_id: str, task: Task, plan: Plan) -> Path:
        workspace_path = self.store.workspace_dir(run_id)
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "task.json").write_text(json.dumps(serialize(task), indent=2, sort_keys=True) + "\n")
        (workspace_path / "plan.json").write_text(json.dumps(serialize(plan), indent=2, sort_keys=True) + "\n")
        return workspace_path

    def _record_preflight_snapshot(self, task_id: str, phase: PreflightPhase, role: Role, resolution: Any) -> None:
        snapshot = PreflightSnapshot(
            id=generate_id("preflight"),
            task_id=task_id,
            phase=phase,
            role=role.value,
            selected_assignment=resolution.selected_assignment,
            preflight_results=resolution.results,
            fallback_event=resolution.fallback_event,
            created_at=utc_now(),
        )
        self.store.save_preflight_snapshot(snapshot)

    def _provider_filter_for_role(self, role: Role, runner_name: str | None) -> Provider | None:
        if role != Role.EXECUTOR or runner_name is None:
            return None
        mapping = {
            "claude_code": Provider.CLAUDE,
            "grok_runner": Provider.GROK,
            "codex_runner": Provider.CODEX,
        }
        return mapping.get(runner_name)

    def _access_mode_filter(self, access_mode_name: str | None) -> AccessMode | None:
        if access_mode_name in (None, "auto"):
            return None
        return AccessMode(access_mode_name)

    def _get_workflow_engine(self) -> WorkflowEngine:
        if self._workflow_engine_instance is None:
            self._workflow_engine_instance = build_workflow_engine(self.store)
        return self._workflow_engine_instance

    def _validate_plan_inputs(self, auto: bool, summary: str | None, steps: list[str] | None) -> None:
        if auto and (summary is not None or steps):
            raise PatchrailError("Use either manual plan inputs or --auto, not both.")
        if not auto and (summary is None or not steps):
            raise PatchrailError("Manual plan creation requires --summary and at least one --step.")

    def _validate_review_inputs(self, auto: bool, verdict: str | None, summary: str | None) -> None:
        if auto and (verdict is not None or summary is not None):
            raise PatchrailError("Use either manual review inputs or --auto, not both.")
        if not auto and (verdict is None or summary is None):
            raise PatchrailError("Manual review requires --verdict and --summary.")

    def _require_assignment(self, task: Task, role: Role, resolution: Any) -> Any:
        if resolution.selected_assignment is None:
            self._append_trace(
                task.id,
                f"{role.value}.preflight_blocked",
                f"No ready {role.value} candidates were available.",
                metadata={"preflight_results": serialize(resolution.results)},
            )
            raise PatchrailError(f"No ready {role.value} candidates were available during preflight.")
        if resolution.selected_assignment.requires_additional_approval:
            existing_request = self._matching_fallback_request(task, role, resolution)
            if existing_request is not None:
                if existing_request.status == FallbackApprovalStatus.APPROVED:
                    self._append_trace(
                        task.id,
                        f"{role.value}.fallback_approved",
                        f"Approved fallback request {existing_request.id} used for role {role.value}.",
                        metadata={"fallback_request_id": existing_request.id},
                    )
                    return resolution.selected_assignment
                if existing_request.status == FallbackApprovalStatus.PENDING:
                    raise PatchrailError(
                        f"{role.value} fallback requires additional approval before proceeding. "
                        f"Request {existing_request.id} is pending. "
                        f"Run `patchrail approve-fallback --task-id {task.id} --rationale ...` to continue."
                    )
                raise PatchrailError(
                    f"{role.value} fallback request {existing_request.id} was rejected. "
                    f"Adjust policy or create a new eligible resolution before retrying."
                )
            request = self.fallback_approval.create_request(
                task=task,
                role=role,
                assignment=resolution.selected_assignment,
                preflight_results=resolution.results,
                fallback_event=resolution.fallback_event,
            )
            self._append_trace(
                task.id,
                f"{role.value}.fallback_blocked",
                f"{role.value} fallback requires additional approval.",
                metadata={
                    "assignment": serialize(resolution.selected_assignment),
                    "preflight_results": serialize(resolution.results),
                    "fallback_event": serialize(resolution.fallback_event) if resolution.fallback_event else None,
                    "fallback_request_id": request.id,
                },
            )
            raise PatchrailError(
                f"{role.value} fallback requires additional approval before proceeding. "
                f"Request {request.id} created. "
                f"Run `patchrail approve-fallback --task-id {task.id} --rationale ...` to continue."
            )
        return resolution.selected_assignment

    def _matching_fallback_request(self, task: Task, role: Role, resolution: Any) -> Any:
        if task.latest_fallback_request_id is None or resolution.fallback_event is None:
            return None
        request = self.store.load_fallback_request(task.latest_fallback_request_id)
        if request.task_id != task.id or request.role != role.value:
            return None
        assignment = resolution.selected_assignment
        if assignment is None:
            return None
        if (
            request.requested_assignment.candidate_name != assignment.candidate_name
            or request.requested_assignment.provider != assignment.provider
            or request.requested_assignment.access_mode != assignment.access_mode
        ):
            return None
        if request.fallback_event.selected_candidate != resolution.fallback_event.selected_candidate:
            return None
        if request.fallback_event.attempted_candidate != resolution.fallback_event.attempted_candidate:
            return None
        return request
