from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import (
    ApprovalRecord,
    ArtifactBundle,
    DecisionTrace,
    FallbackApprovalRequest,
    Plan,
    PreflightSnapshot,
    ReviewResult,
    Run,
    Task,
    serialize,
)


class FilesystemStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._ensure_layout()

    @classmethod
    def from_environment(cls, cwd: Path | None = None) -> FilesystemStore:
        configured = os.getenv("PATCHRAIL_HOME")
        root = Path(configured) if configured else (cwd or Path.cwd()) / ".patchrail"
        return cls(root=root)

    def _ensure_layout(self) -> None:
        for relative in (
            "tasks",
            "plans",
            "runs",
            "reviews",
            "approvals",
            "fallback_requests",
            "preflight_snapshots",
            "artifacts",
            "workspaces",
            "ledgers",
        ):
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def save_task(self, task: Task) -> None:
        self._write_json(self.root / "tasks" / f"{task.id}.json", serialize(task))

    def load_task(self, task_id: str) -> Task:
        return Task.from_dict(self._read_json(self.root / "tasks" / f"{task_id}.json"))

    def list_tasks(self) -> list[Task]:
        return self._list_records(self.root / "tasks", Task.from_dict, "created_at")

    def save_plan(self, plan: Plan) -> None:
        self._write_json(self.root / "plans" / f"{plan.id}.json", serialize(plan))

    def load_plan(self, plan_id: str) -> Plan:
        return Plan.from_dict(self._read_json(self.root / "plans" / f"{plan_id}.json"))

    def list_plans(self) -> list[Plan]:
        return self._list_records(self.root / "plans", Plan.from_dict, "created_at")

    def save_run(self, run: Run) -> None:
        self._write_json(self.root / "runs" / f"{run.id}.json", serialize(run))

    def load_run(self, run_id: str) -> Run:
        return Run.from_dict(self._read_json(self.root / "runs" / f"{run_id}.json"))

    def list_runs(self) -> list[Run]:
        return self._list_records(self.root / "runs", Run.from_dict, "created_at")

    def save_review(self, review: ReviewResult) -> None:
        self._write_json(self.root / "reviews" / f"{review.id}.json", serialize(review))

    def load_review(self, review_id: str) -> ReviewResult:
        return ReviewResult.from_dict(self._read_json(self.root / "reviews" / f"{review_id}.json"))

    def list_reviews(self) -> list[ReviewResult]:
        return self._list_records(self.root / "reviews", ReviewResult.from_dict, "created_at")

    def save_approval(self, approval: ApprovalRecord) -> None:
        self._write_json(self.root / "approvals" / f"{approval.id}.json", serialize(approval))

    def load_approval(self, approval_id: str) -> ApprovalRecord:
        return ApprovalRecord.from_dict(self._read_json(self.root / "approvals" / f"{approval_id}.json"))

    def list_approvals(self) -> list[ApprovalRecord]:
        return self._list_records(self.root / "approvals", ApprovalRecord.from_dict, "created_at")

    def save_fallback_request(self, request: FallbackApprovalRequest) -> None:
        self._write_json(self.root / "fallback_requests" / f"{request.id}.json", serialize(request))

    def load_fallback_request(self, request_id: str) -> FallbackApprovalRequest:
        return FallbackApprovalRequest.from_dict(self._read_json(self.root / "fallback_requests" / f"{request_id}.json"))

    def list_fallback_requests(self) -> list[FallbackApprovalRequest]:
        return self._list_records(
            self.root / "fallback_requests",
            FallbackApprovalRequest.from_dict,
            "created_at",
        )

    def save_preflight_snapshot(self, snapshot: PreflightSnapshot) -> None:
        self._write_json(self.root / "preflight_snapshots" / f"{snapshot.id}.json", serialize(snapshot))

    def load_preflight_snapshot(self, snapshot_id: str) -> PreflightSnapshot:
        return PreflightSnapshot.from_dict(
            self._read_json(self.root / "preflight_snapshots" / f"{snapshot_id}.json")
        )

    def list_preflight_snapshots(self) -> list[PreflightSnapshot]:
        return self._list_records(
            self.root / "preflight_snapshots",
            PreflightSnapshot.from_dict,
            "created_at",
        )

    def save_artifact_bundle(self, bundle: ArtifactBundle) -> None:
        bundle_dir = self.artifact_dir(bundle.run_id)
        bundle_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(bundle_dir / "bundle.json", serialize(bundle))

    def load_artifact_bundle(self, run_id: str) -> ArtifactBundle:
        return ArtifactBundle.from_dict(self._read_json(self.artifact_dir(run_id) / "bundle.json"))

    def list_artifact_bundles(self) -> list[ArtifactBundle]:
        bundles = [
            ArtifactBundle.from_dict(json.loads(path.read_text()))
            for path in sorted((self.root / "artifacts").glob("*/bundle.json"))
        ]
        return sorted(bundles, key=lambda item: item.created_at, reverse=True)

    def artifact_dir(self, run_id: str) -> Path:
        return self.root / "artifacts" / run_id

    def workspace_dir(self, run_id: str) -> Path:
        return self.root / "workspaces" / run_id

    def append_decision_trace(self, trace: DecisionTrace) -> None:
        self._append_jsonl(self.root / "ledgers" / "decision-trace.jsonl", serialize(trace))

    def append_approval_ledger(self, approval: ApprovalRecord) -> None:
        self._append_jsonl(self.root / "ledgers" / "approval-ledger.jsonl", serialize(approval))

    def append_fallback_approval_ledger(self, request: FallbackApprovalRequest) -> None:
        self._append_jsonl(self.root / "ledgers" / "fallback-approval-ledger.jsonl", serialize(request))

    def read_stdout_log(self, run_id: str) -> str:
        log_path = self.artifact_dir(run_id) / "stdout.log"
        if not log_path.exists():
            raise PatchrailError(f"No logs found for run {run_id}.")
        return log_path.read_text()

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            stem = path.stem
            raise PatchrailError(f"Unknown record '{stem}'.")
        return json.loads(path.read_text())

    def _list_records(self, directory: Path, factory: Any, sort_field: str) -> list[Any]:
        records = [factory(json.loads(path.read_text())) for path in sorted(directory.glob("*.json"))]
        return sorted(records, key=lambda item: getattr(item, sort_field), reverse=True)
