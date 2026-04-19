from __future__ import annotations

from typing import Any


def render_payload(args: Any, payload: dict[str, Any]) -> str:
    if args.command == "config" and getattr(args, "config_command", None) == "init":
        return _render_config_init(payload)
    if args.command == "doctor":
        return _render_doctor(payload)
    if args.command == "task" and getattr(args, "task_command", None) == "create":
        return _render_task_create(payload)
    if args.command == "plan":
        return _render_plan(payload)
    if args.command == "preflight":
        return _render_preflight(payload)
    if args.command == "run":
        return _render_run(payload)
    if args.command == "review":
        return _render_review(payload)
    if args.command in {"approve", "reject"}:
        return _render_approval(payload)
    if args.command in {"approve-fallback", "reject-fallback"}:
        return _render_fallback(payload)
    if args.command == "status":
        return _render_status(payload)
    if args.command == "logs":
        return _render_logs(payload)
    if args.command == "artifacts":
        return _render_artifacts(payload)
    if args.command == "list":
        return _render_list(getattr(args, "list_command", ""), payload)
    return _render_unknown(payload)


def _render_config_init(payload: dict[str, Any]) -> str:
    config = payload["config"]
    workflow = payload["workflow"]
    return "\n".join(
        [
            "Initialized Patchrail config",
            f"Preset: {config['preset']}",
            f"Workflow backend: {workflow['backend']}",
            f"Config path: {config['path']}",
            f"Workflow path: {workflow['path']}",
            "Next:",
            "  patchrail doctor",
            "  sh scripts/local_smoke_test.sh",
        ]
    )


def _render_doctor(payload: dict[str, Any]) -> str:
    doctor = payload["doctor"]
    lines = [
        "Patchrail Doctor",
        f"Home: {doctor['patchrail_home']}",
        f"Config: {'ready' if doctor['config_initialized'] else 'missing'}",
        f"Workflow backend: {doctor['workflow_backend'] or 'uninitialized'}",
    ]
    preflight = doctor.get("preflight") or {}
    if preflight:
        lines.append("Resolved candidates:")
        for role in ("planner", "reviewer", "executor"):
            item = preflight.get(role)
            if not item:
                continue
            selected = item.get("selected_candidate")
            if selected is None:
                lines.append(f"  {role.capitalize()}: no ready candidate")
                continue
            lines.append(
                f"  {role.capitalize()}: {selected['candidate_name']} "
                f"({selected['provider']} {selected['access_mode']})"
            )
    lines.append("Next:")
    for step in doctor["next_steps"]:
        lines.append(f"  {step}")
    return "\n".join(lines)


def _render_task_create(payload: dict[str, Any]) -> str:
    task = payload["task"]
    return "\n".join(
        [
            f"Created task {task['id']}",
            f"Title: {task['title']}",
            f"State: {task['state']}",
            f"Description: {task['description']}",
        ]
    )


def _render_plan(payload: dict[str, Any]) -> str:
    plan = payload["plan"]
    task = payload["task"]
    lines = [
        f"Stored plan {plan['id']} for task {task['id']}",
        f"Task state: {task['state']}",
        f"Summary: {plan['summary']}",
        "Steps:",
    ]
    for index, step in enumerate(plan["steps"], start=1):
        lines.append(f"  {index}. {step}")
    if plan.get("workflow_backend"):
        lines.append(f"Workflow backend: {plan['workflow_backend']}")
    return "\n".join(lines)


def _render_preflight(payload: dict[str, Any]) -> str:
    lines = [f"Preflight: {payload['role']}"]
    selected = payload.get("selected_candidate")
    if selected:
        lines.append(
            f"Selected: {selected['candidate_name']} ({selected['provider']} {selected['access_mode']})"
        )
    else:
        lines.append("Selected: no ready candidate")
    lines.append("Candidates:")
    for result in payload.get("results", []):
        state = "ready" if result["ready"] else "blocked"
        lines.append(
            f"  {result['candidate_name']}: {state} ({result['provider']} {result['access_mode']})"
        )
    if payload.get("fallback_event"):
        lines.append("Fallback: additional approval required")
    return "\n".join(lines)


def _render_run(payload: dict[str, Any]) -> str:
    run = payload["run"]
    task = payload["task"]
    bundle = payload["artifact_bundle"]
    return "\n".join(
        [
            f"Completed run {run['id']} for task {task['id']}",
            f"Runner: {run['runner_assignment']['runner_name']}",
            f"Task state: {task['state']}",
            f"Workspace: {run['workspace_path']}",
            f"Artifact bundle: {bundle['run_id']}",
            f"Exit code: {run['exit_code']}",
        ]
    )


def _render_review(payload: dict[str, Any]) -> str:
    review = payload["review"]
    task = payload["task"]
    lines = [
        f"Recorded review {review['id']} for run {review['run_id']}",
        f"Verdict: {review['verdict']}",
        f"Task state: {task['state']}",
        f"Summary: {review['summary']}",
    ]
    if review.get("workflow_backend"):
        lines.append(f"Workflow backend: {review['workflow_backend']}")
    return "\n".join(lines)


def _render_approval(payload: dict[str, Any]) -> str:
    approval = payload["approval"]
    task = payload["task"]
    return "\n".join(
        [
            f"Recorded approval {approval['id']}",
            f"Decision: {approval['decision']}",
            f"Task: {task['id']}",
            f"Task state: {task['state']}",
            f"Rationale: {approval['rationale']}",
        ]
    )


def _render_fallback(payload: dict[str, Any]) -> str:
    request = payload["fallback_request"]
    task = payload["task"]
    return "\n".join(
        [
            f"Updated fallback request {request['id']}",
            f"Role: {request['role']}",
            f"Status: {request['status']}",
            f"Task: {task['id']}",
            f"Rationale: {request.get('rationale') or ''}",
        ]
    )


def _render_status(payload: dict[str, Any]) -> str:
    task = payload["task"]
    lines = [
        f"Task {task['id']}: {task['title']}",
        f"State: {task['state']}",
        f"Description: {task['description']}",
    ]
    if "plan" in payload:
        lines.append(f"Plan: {payload['plan']['id']} | {payload['plan']['summary']}")
    if "latest_run" in payload:
        run = payload["latest_run"]
        lines.append(f"Latest run: {run['id']} | exit {run['exit_code']} | {run['status']}")
    if "latest_review" in payload:
        review = payload["latest_review"]
        lines.append(f"Latest review: {review['id']} | {review['verdict']} | {review['summary']}")
    if "latest_approval" in payload:
        approval = payload["latest_approval"]
        lines.append(f"Latest approval: {approval['id']} | {approval['decision']}")
    if "latest_fallback_request" in payload:
        request = payload["latest_fallback_request"]
        lines.append(f"Fallback request: {request['id']} | {request['status']}")
    return "\n".join(lines)


def _render_logs(payload: dict[str, Any]) -> str:
    lines = [f"Logs for run {payload['run_id']}", "", payload["stdout"].rstrip()]
    return "\n".join(lines).rstrip()


def _render_artifacts(payload: dict[str, Any]) -> str:
    bundle = payload["artifact_bundle"]
    lines = [f"Artifacts for run {bundle['run_id']}"]
    for name, path in sorted(bundle["files"].items()):
        artifact = bundle.get("artifacts", {}).get(name)
        if artifact:
            lines.append(f"  {name}: {path} [{artifact['logical_kind']}]")
        else:
            lines.append(f"  {name}: {path}")
    return "\n".join(lines)


def _render_list(list_command: str, payload: dict[str, Any]) -> str:
    key = {
        "tasks": "tasks",
        "plans": "plans",
        "runs": "runs",
        "reviews": "reviews",
        "approvals": "approvals",
        "fallback-requests": "fallback_requests",
        "preflight-snapshots": "preflight_snapshots",
        "artifact-bundles": "artifact_bundles",
    }[list_command]
    items = payload.get(key, [])
    title = key.replace("_", " ")
    lines = [f"{title.title()}: {len(items)}"]
    if not items:
        return "\n".join(lines)
    for item in items:
        lines.append(f"  {_list_item_summary(key, item)}")
    return "\n".join(lines)


def _list_item_summary(key: str, item: dict[str, Any]) -> str:
    if key == "tasks":
        return f"{item['id']} | {item['state']} | {item['title']}"
    if key == "plans":
        return f"{item['id']} | task={item['task_id']} | {item['summary']}"
    if key == "runs":
        return f"{item['id']} | task={item['task_id']} | exit={item['exit_code']} | {item['status']}"
    if key == "reviews":
        return f"{item['id']} | task={item['task_id']} | {item['verdict']} | {item['summary']}"
    if key == "approvals":
        return f"{item['id']} | task={item['task_id']} | {item['decision']}"
    if key == "fallback_requests":
        return f"{item['id']} | task={item['task_id']} | {item['role']} | {item['status']}"
    if key == "preflight_snapshots":
        return f"{item['id']} | task={item['task_id']} | {item['phase']} | {item['role']}"
    if key == "artifact_bundles":
        return f"{item['run_id']} | {item['summary']}"
    return str(item)


def _render_unknown(payload: dict[str, Any]) -> str:
    return str(payload)
