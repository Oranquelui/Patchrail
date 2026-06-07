from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from patchrail.models.entities import VerificationStatus, serialize
from patchrail.storage.filesystem import FilesystemStore


class ApprovalPacketService:
    def __init__(self, store: FilesystemStore) -> None:
        self.store = store

    def build_packet(self, task_id: str) -> dict[str, Any]:
        task = self.store.load_task(task_id)
        plan = self.store.load_plan(task.plan_id) if task.plan_id else None
        latest_run = self.store.load_run(task.latest_run_id) if task.latest_run_id else None
        latest_bundle = self.store.load_artifact_bundle(task.latest_run_id) if task.latest_run_id else None
        latest_review = self.store.load_review(task.latest_review_id) if task.latest_review_id else None
        latest_approval = self.store.load_approval(task.latest_approval_id) if task.latest_approval_id else None
        verifications = [
            verification
            for verification in self.store.list_verifications()
            if latest_run is not None and verification.run_id == latest_run.id
        ]
        latest_verification = verifications[0] if verifications else None

        return {
            "task": serialize(task),
            "delivery_contract": {
                "planning_briefs": serialize(plan.planning_briefs) if plan else [],
                "status": "captured" if plan and plan.planning_briefs else "not_captured",
            },
            "plan": serialize(plan) if plan else None,
            "run": serialize(latest_run) if latest_run else None,
            "artifact_bundle": serialize(latest_bundle) if latest_bundle else None,
            "verifications": serialize(verifications),
            "latest_verification": serialize(latest_verification) if latest_verification else None,
            "review": serialize(latest_review) if latest_review else None,
            "approval": serialize(latest_approval) if latest_approval else None,
            "unresolved_gaps": self._unresolved_gaps(
                has_run=latest_run is not None,
                latest_verification=latest_verification,
                has_review=latest_review is not None,
                has_approval=latest_approval is not None,
            ),
        }

    def render_markdown(self, packet: dict[str, Any]) -> str:
        task = packet["task"]
        plan = packet.get("plan")
        run = packet.get("run")
        bundle = packet.get("artifact_bundle")
        verifications = packet.get("verifications", [])
        review = packet.get("review")
        approval = packet.get("approval")
        gaps = packet.get("unresolved_gaps", [])
        lines = [
            "# Patchrail Approval Packet",
            "",
            "## Task",
            f"- ID: {task['id']}",
            f"- Title: {task['title']}",
            f"- State: {task['state']}",
            f"- Description: {task['description']}",
            "",
            "## Delivery Contract",
        ]
        briefs = packet["delivery_contract"]["planning_briefs"]
        if briefs:
            for brief in briefs:
                lines.append(f"- {brief['kind']}: {brief['id']} ({brief['sha256']})")
        else:
            lines.append("- No planning briefs captured for this task.")
        lines.extend(["", "## Plan"])
        if plan:
            lines.append(f"- ID: {plan['id']}")
            lines.append(f"- Summary: {plan['summary']}")
            for index, step in enumerate(plan["steps"], start=1):
                lines.append(f"- Step {index}: {step}")
        else:
            lines.append("- No plan recorded.")
        lines.extend(["", "## Run"])
        if run:
            lines.append(f"- ID: {run['id']}")
            lines.append(f"- Runner: {run['runner_assignment']['runner_name']}")
            lines.append(f"- Exit code: {run['exit_code']}")
            lines.append(f"- Workspace: {run['workspace_path']}")
        else:
            lines.append("- No run recorded.")
        lines.extend(["", "## Artifacts"])
        if bundle:
            lines.append(f"- Bundle: {bundle['run_id']}")
            artifacts = bundle.get("artifacts", {})
            for name, path in sorted(bundle["files"].items()):
                artifact = artifacts.get(name)
                if artifact:
                    lines.append(f"- {name}: {path} [{artifact['logical_kind']}]")
                else:
                    lines.append(f"- {name}: {path}")
        else:
            lines.append("- No artifact bundle recorded.")
        lines.extend(["", "## Verification"])
        if verifications:
            for verification in verifications:
                lines.append(
                    f"- {verification['id']}: {verification['status']} "
                    f"(exit {verification['exit_code']}) `{verification['command']}`"
                )
        else:
            lines.append("- No verification recorded for the latest run.")
        lines.extend(["", "## Review"])
        if review:
            lines.append(f"- {review['id']}: {review['verdict']} - {review['summary']}")
        else:
            lines.append("- No review recorded.")
        lines.extend(["", "## Approval"])
        if approval:
            lines.append(f"- {approval['id']}: {approval['decision']} - {approval['rationale']}")
        else:
            lines.append("- No approval decision recorded.")
        lines.extend(["", "## Unresolved Gaps"])
        if gaps:
            for gap in gaps:
                lines.append(f"- {gap}")
        else:
            lines.append("- None.")
        return "\n".join(lines) + "\n"

    def render_json(self, packet: dict[str, Any]) -> str:
        return json.dumps(packet, indent=2, sort_keys=True) + "\n"

    def export_packet(self, task_id: str, output_path: str, output_format: str) -> dict[str, Any]:
        packet = self.build_packet(task_id)
        content = self.render_json(packet) if output_format == "json" else self.render_markdown(packet)
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return {"packet": packet, "content": content, "output_path": str(path), "format": output_format}

    def _unresolved_gaps(
        self,
        *,
        has_run: bool,
        latest_verification: Any,
        has_review: bool,
        has_approval: bool,
    ) -> list[str]:
        gaps: list[str] = []
        if not has_run:
            gaps.append("No run recorded.")
            return gaps
        if latest_verification is None:
            gaps.append("No verification recorded for latest run.")
        elif latest_verification.status == VerificationStatus.FAILED:
            gaps.append("Latest verification failed.")
        if not has_review:
            gaps.append("No review recorded.")
        if not has_approval:
            gaps.append("No approval decision recorded.")
        return gaps
