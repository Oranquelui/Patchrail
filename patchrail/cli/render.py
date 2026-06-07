from __future__ import annotations

import shutil
import sys
from typing import Any


def render_payload(args: Any, payload: dict[str, Any]) -> str:
    if args.command == "start":
        return _render_start(payload)
    if args.command == "config" and getattr(args, "config_command", None) == "init":
        return _render_config_init(payload)
    if args.command == "setup":
        return _render_setup(payload)
    if args.command == "doctor":
        return _render_doctor(payload)
    if args.command == "task" and getattr(args, "task_command", None) == "create":
        return _render_task_create(payload)
    if args.command == "brief":
        return _render_brief(getattr(args, "brief_command", ""), payload)
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
    if args.command == "verify":
        return _render_verification(payload)
    if args.command == "packet":
        return _render_packet(getattr(args, "packet_command", ""), payload)
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


def _render_setup(payload: dict[str, Any]) -> str:
    setup = payload["setup"]
    lines = [
        _style("Patchrail Setup", "title"),
        _style("local-first supervised agent setup", "muted"),
        "",
        _panel(
            "Runtime",
            [
                f"Scope: {setup['scope']}",
                f"Config: {'created' if setup['config_created'] else 'existing'}",
                f"Workflow backend: {setup['workflow_backend']}",
            ],
        ),
    ]
    if setup["scope"] == "runtime":
        preflight = setup.get("preflight") or {}
        candidate_lines: list[str] = []
        for role in ("planner", "reviewer", "executor"):
            item = preflight.get(role)
            if not item:
                continue
            selected = item.get("selected_candidate")
            if selected is None:
                candidate_lines.append(f"{role.capitalize()}: no ready candidate")
            else:
                candidate_lines.append(
                    f"{role.capitalize()}: {selected['candidate_name']} "
                    f"({selected['provider']} {selected['access_mode']})"
                )
        if candidate_lines:
            lines.extend(["", _panel("Checks", candidate_lines)])
    if setup["scope"] == "project":
        task = setup["task"]
        brief_lines = [
            f"Task: {task['id']}",
            f"Title: {task['title']}",
        ]
        for kind, path in setup["brief_files"].items():
            brief_lines.append(f"{kind} source: {path}")
        if not setup["briefs"]:
            brief_lines.append("Persisted briefs: none yet; edit sources, then run brief create before plan.")
        for brief in setup["briefs"]:
            brief_lines.append(f"{brief['kind']}: {brief['id']} -> {setup['brief_files'][brief['kind']]}")
        lines.extend(["", _panel("Project", brief_lines)])
    lines.extend(["", _panel("Next", [f"{index}. {step}" for index, step in enumerate(setup["next_steps"], start=1)])])
    return "\n".join(lines)


def _render_start(payload: dict[str, Any]) -> str:
    start = payload["start"]
    lines = _brand_header()
    lines.extend(
        [
            "",
            _panel(
                "Project",
                [
                    f"Config: {'created' if start['config_created'] else 'existing'}",
                    f"Workflow backend: {start['workflow_backend']}",
                ],
            ),
        ]
    )
    preflight = start.get("preflight") or {}
    if preflight:
        candidate_lines: list[str] = []
        for role in ("planner", "reviewer", "executor"):
            item = preflight.get(role)
            if not item or item.get("selected_candidate") is None:
                continue
            selected = item["selected_candidate"]
            candidate_lines.append(
                f"{role.capitalize()}: {selected['candidate_name']} "
                f"({selected['provider']} {selected['access_mode']})"
            )
        lines.extend(["", _panel("Resolved Candidates", candidate_lines)])
    lines.extend(
        [
            "",
            _panel(
                "Next",
                [
                    f"1. {start['next_steps'][0]}",
                    f"2. {start['next_steps'][1]}",
                    f"3. {start['next_steps'][2]}",
                    "Tip: in the interactive shell, type `help` or `exit`.",
                    "Tip: use `patchrail --json ...` for automation.",
                    "Tip: `.patchrail` is a local data directory, not a shell command.",
                ],
            ),
        ]
    )
    return "\n".join(lines)


def _brand_header() -> list[str]:
    return [
        _style(" ____       _       _                _ _ ", "logo"),
        _style("|  _ \\ __ _| |_ ___| |__  _ __ __ _(_) |", "logo"),
        _style("| |_) / _` | __/ __| '_ \\| '__/ _` | | |", "logo"),
        _style("|  __/ (_| | || (__| | | | | | (_| | | |", "logo"),
        _style("|_|   \\__,_|\\__\\___|_| |_|_|  \\__,_|_|_|", "logo"),
        _style("Patchrail Start", "title"),
        _style("supervised coding-agent control plane", "muted"),
    ]


def _render_doctor(payload: dict[str, Any]) -> str:
    doctor = payload["doctor"]
    lines = [
        _style("Patchrail Doctor", "title"),
        _style("readiness and policy summary", "muted"),
        "",
        _panel(
            "Status",
            [
                f"Config: {'ready' if doctor['config_initialized'] else 'missing'}",
                f"Workflow backend: {doctor['workflow_backend'] or 'uninitialized'}",
            ],
        ),
    ]
    preflight = doctor.get("preflight") or {}
    if preflight:
        candidate_lines: list[str] = []
        for role in ("planner", "reviewer", "executor"):
            item = preflight.get(role)
            if not item:
                continue
            selected = item.get("selected_candidate")
            if selected is None:
                candidate_lines.append(f"{role.capitalize()}: no ready candidate")
                continue
            candidate_lines.append(
                f"  {role.capitalize()}: {selected['candidate_name']} "
                f"({selected['provider']} {selected['access_mode']})"
            )
        lines.extend(["", _panel("Resolved Candidates", candidate_lines)])
    lines.extend(
        [
            "",
            _panel("Next", [f"1. {step}" for step in doctor["next_steps"]]),
        ]
    )
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


def _render_brief(brief_command: str, payload: dict[str, Any]) -> str:
    if brief_command == "create":
        brief = payload["brief"]
        task = payload["task"]
        return "\n".join(
            [
                f"Stored {brief['kind']} brief {brief['id']} for task {task['id']}",
                f"Source: {brief['source_path']}",
                f"Storage: {brief['storage_path']}",
                f"SHA256: {brief['sha256']}",
            ]
        )
    if brief_command == "list":
        briefs = payload["briefs"]
        lines = [f"Briefs: {len(briefs)}"]
        for brief in briefs:
            attached = brief.get("attached_plan_id") or "pending"
            lines.append(f"  {brief['id']} | {brief['kind']} | plan={attached}")
        return "\n".join(lines)
    if brief_command == "show":
        brief = payload["brief"]
        return "\n".join(
            [
                f"Brief {brief['id']} ({brief['kind']})",
                f"Task: {brief['task_id']}",
                f"Source: {brief['source_path']}",
                f"Storage: {brief['storage_path']}",
                "",
                brief["content"].rstrip(),
            ]
        ).rstrip()
    return _render_unknown(payload)


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
    if plan.get("planning_briefs"):
        lines.append("Planning briefs:")
        for brief in plan["planning_briefs"]:
            lines.append(f"  {brief['kind']}: {brief['id']}")
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
        if payload["plan"].get("planning_briefs"):
            brief_labels = ", ".join(
                f"{brief['kind']}:{brief['id']}" for brief in payload["plan"]["planning_briefs"]
            )
            lines.append(f"Planning briefs: {brief_labels}")
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


def _render_verification(payload: dict[str, Any]) -> str:
    verification = payload["verification"]
    return "\n".join(
        [
            f"Recorded verification {verification['id']} for run {verification['run_id']}",
            f"Status: {verification['status']}",
            f"Exit code: {verification['exit_code']}",
            f"Command: {verification['command']}",
            f"Stdout: {verification['stdout_path']}",
            f"Stderr: {verification['stderr_path']}",
        ]
    )


def _render_packet(packet_command: str, payload: dict[str, Any]) -> str:
    if packet_command == "show":
        return payload["content"].rstrip()
    if packet_command == "export":
        return "\n".join(
            [
                "Exported approval packet",
                f"Format: {payload['format']}",
                f"Output: {payload['output_path']}",
            ]
        )
    return _render_unknown(payload)


def _render_list(list_command: str, payload: dict[str, Any]) -> str:
    if list_command == "review-queue":
        return _render_review_queue(payload)
    key = {
        "tasks": "tasks",
        "plans": "plans",
        "runs": "runs",
        "reviews": "reviews",
        "approvals": "approvals",
        "fallback-requests": "fallback_requests",
        "preflight-snapshots": "preflight_snapshots",
        "artifact-bundles": "artifact_bundles",
        "verifications": "verifications",
    }[list_command]
    items = payload.get(key, [])
    title = key.replace("_", " ")
    lines = [f"{title.title()}: {len(items)}"]
    if not items:
        return "\n".join(lines)
    for item in items:
        lines.append(f"  {_list_item_summary(key, item)}")
    return "\n".join(lines)


def _render_review_queue(payload: dict[str, Any]) -> str:
    queue = payload["review_queue"]
    lines = ["Review Queue"]
    for group in ("needs_verification", "failed_verification", "ready_for_review", "awaiting_approval", "approved"):
        items = queue[group]
        lines.append(f"{group}: {len(items)}")
        for item in items:
            lines.append(f"  {item['id']} | {item['state']} | {item['title']}")
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
    if key == "verifications":
        return f"{item['id']} | run={item['run_id']} | {item['status']} | exit={item['exit_code']}"
    return str(item)


def _render_unknown(payload: dict[str, Any]) -> str:
    return str(payload)


def _panel(title: str, lines: list[str]) -> str:
    width = max(_terminal_width() - 2, 60)
    inner_width = min(max((max((len(line) for line in lines), default=0) + 2), len(title) + 2), width - 2)
    border = "+" + "-" * inner_width + "+"
    rendered = [border, "| " + title.ljust(inner_width - 1) + "|", border]
    for line in lines:
        fitted = _fit_line(line, inner_width - 1)
        rendered.append("| " + fitted.ljust(inner_width - 1) + "|")
    rendered.append(border)
    return "\n".join(_style(line, "panel") for line in rendered)


def _terminal_width() -> int:
    return shutil.get_terminal_size(fallback=(100, 24)).columns


def _fit_line(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def _style(text: str, style: str) -> str:
    if not sys.stdout.isatty():
        return text
    colors = {
        "logo": "\033[38;5;213m",
        "title": "\033[1;96m",
        "muted": "\033[0;37m",
        "panel": "\033[0;36m",
    }
    reset = "\033[0m"
    color = colors.get(style, "")
    if not color:
        return text
    return f"{color}{text}{reset}"
