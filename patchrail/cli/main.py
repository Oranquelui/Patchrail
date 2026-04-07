from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from patchrail.core.exceptions import PatchrailError
from patchrail.core.service import PatchrailApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="patchrail")
    subparsers = parser.add_subparsers(dest="command", required=True)

    task_parser = subparsers.add_parser("task")
    task_subparsers = task_parser.add_subparsers(dest="task_command", required=True)
    task_create = task_subparsers.add_parser("create")
    task_create.add_argument("--title", required=True)
    task_create.add_argument("--description", required=True)

    config_parser = subparsers.add_parser("config")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_subparsers.add_parser("init")

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--task-id", required=True)
    plan_parser.add_argument("--summary", required=True)
    plan_parser.add_argument("--step", action="append", required=True)

    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--role", choices=["planner", "reviewer", "executor"], required=True)
    preflight_parser.add_argument("--runner", choices=["claude_code", "grok_runner", "codex_runner", "auto"])

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--task-id", required=True)
    run_parser.add_argument("--runner", choices=["claude_code", "grok_runner", "codex_runner", "auto"], required=True)

    status_parser = subparsers.add_parser("status")
    status_group = status_parser.add_mutually_exclusive_group(required=True)
    status_group.add_argument("--task-id")
    status_group.add_argument("--run-id")

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--run-id", required=True)
    review_parser.add_argument("--verdict", choices=["pass", "fail"], required=True)
    review_parser.add_argument("--summary", required=True)

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("--task-id", required=True)
    approve_parser.add_argument("--rationale", required=True)

    approve_fallback_parser = subparsers.add_parser("approve-fallback")
    approve_fallback_parser.add_argument("--task-id", required=True)
    approve_fallback_parser.add_argument("--rationale", required=True)

    reject_parser = subparsers.add_parser("reject")
    reject_parser.add_argument("--task-id", required=True)
    reject_parser.add_argument("--rationale", required=True)

    reject_fallback_parser = subparsers.add_parser("reject-fallback")
    reject_fallback_parser.add_argument("--task-id", required=True)
    reject_fallback_parser.add_argument("--rationale", required=True)

    logs_parser = subparsers.add_parser("logs")
    logs_parser.add_argument("--run-id", required=True)

    artifacts_parser = subparsers.add_parser("artifacts")
    artifacts_parser.add_argument("--run-id", required=True)

    list_parser = subparsers.add_parser("list")
    list_subparsers = list_parser.add_subparsers(dest="list_command", required=True)
    list_subparsers.add_parser("tasks")
    list_plans = list_subparsers.add_parser("plans")
    list_plans.add_argument("--task-id")
    list_runs = list_subparsers.add_parser("runs")
    list_runs.add_argument("--task-id")
    list_reviews = list_subparsers.add_parser("reviews")
    list_reviews.add_argument("--task-id")
    list_approvals = list_subparsers.add_parser("approvals")
    list_approvals.add_argument("--task-id")
    list_fallbacks = list_subparsers.add_parser("fallback-requests")
    list_fallbacks.add_argument("--task-id")
    list_preflight = list_subparsers.add_parser("preflight-snapshots")
    list_preflight.add_argument("--task-id")

    return parser


def execute(args: argparse.Namespace) -> dict[str, Any]:
    app = PatchrailApp.from_environment()

    if args.command == "task" and args.task_command == "create":
        return app.create_task(title=args.title, description=args.description)
    if args.command == "config" and args.config_command == "init":
        return app.init_config()
    if args.command == "plan":
        return app.create_plan(task_id=args.task_id, summary=args.summary, steps=args.step)
    if args.command == "preflight":
        return app.preflight(role_name=args.role, runner_name=args.runner)
    if args.command == "run":
        return app.run_task(task_id=args.task_id, runner_name=args.runner)
    if args.command == "status":
        return app.get_status(task_id=args.task_id, run_id=args.run_id)
    if args.command == "review":
        return app.review_run(run_id=args.run_id, verdict=args.verdict, summary=args.summary)
    if args.command == "approve":
        return app.approve_task(task_id=args.task_id, rationale=args.rationale)
    if args.command == "approve-fallback":
        return app.approve_fallback(task_id=args.task_id, rationale=args.rationale)
    if args.command == "reject":
        return app.reject_task(task_id=args.task_id, rationale=args.rationale)
    if args.command == "reject-fallback":
        return app.reject_fallback(task_id=args.task_id, rationale=args.rationale)
    if args.command == "logs":
        return app.get_logs(run_id=args.run_id)
    if args.command == "artifacts":
        return app.get_artifacts(run_id=args.run_id)
    if args.command == "list" and args.list_command == "tasks":
        return app.list_tasks()
    if args.command == "list" and args.list_command == "plans":
        return app.list_plans(task_id=args.task_id)
    if args.command == "list" and args.list_command == "runs":
        return app.list_runs(task_id=args.task_id)
    if args.command == "list" and args.list_command == "reviews":
        return app.list_reviews(task_id=args.task_id)
    if args.command == "list" and args.list_command == "approvals":
        return app.list_approvals(task_id=args.task_id)
    if args.command == "list" and args.list_command == "fallback-requests":
        return app.list_fallback_requests(task_id=args.task_id)
    if args.command == "list" and args.list_command == "preflight-snapshots":
        return app.list_preflight_snapshots(task_id=args.task_id)
    raise PatchrailError("Unsupported command.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        payload = execute(args)
    except PatchrailError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def run() -> None:
    raise SystemExit(main())
