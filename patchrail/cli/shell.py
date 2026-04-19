from __future__ import annotations

import argparse
import json
import shlex
import sys
from types import SimpleNamespace
from typing import Any, TextIO

from patchrail.cli.render import render_payload
from patchrail.core.exceptions import PatchrailError
from patchrail.core.service import PatchrailApp


def should_start_shell(args: argparse.Namespace) -> bool:
    if args.command != "start":
        return False
    if getattr(args, "json", False) or getattr(args, "once", False):
        return False
    return _isatty(sys.stdin) and _isatty(sys.stdout)


def run_start_shell(
    app: PatchrailApp,
    start_payload: dict[str, Any],
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    from patchrail.cli.main import build_parser, execute

    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr
    parser = build_parser()

    _write_block(output_stream, render_payload(_render_args("start"), start_payload))
    _write_block(output_stream, _shell_welcome())

    while True:
        output_stream.write("patchrail> ")
        output_stream.flush()
        raw_command = input_stream.readline()
        if raw_command == "":
            _write_line(output_stream, "Exiting Patchrail shell.")
            return 0

        command = _normalize_shell_command(raw_command)
        if command is None:
            continue
        if command in {"exit", "quit", "q"}:
            _write_line(output_stream, "Exiting Patchrail shell.")
            return 0
        if command == "help":
            _write_block(output_stream, _shell_help())
            continue

        try:
            args = parser.parse_args(shlex.split(command))
        except SystemExit:
            _write_line(error_stream, "Invalid command. Type `help` or `/help`.")
            continue

        try:
            payload = execute(args, app=app)
        except PatchrailError as exc:
            _write_line(error_stream, str(exc))
            continue

        if getattr(args, "json", False):
            _write_block(output_stream, json.dumps(payload, indent=2, sort_keys=True))
        else:
            _write_block(output_stream, render_payload(args, payload))


def _normalize_shell_command(raw_command: str) -> str | None:
    command = raw_command.strip()
    if not command:
        return None
    if command in {"-h", "--help", "?", "/help"}:
        return "help"
    if command in {"/exit", "/quit"}:
        return "exit"
    aliases = {
        "/doctor": "doctor",
        "/home": "start --once",
        "/start": "start --once",
        "/tasks": "list tasks",
    }
    if command in aliases:
        return aliases[command]
    if command == "patchrail":
        return "help"
    if command.startswith("patchrail "):
        return command.split(" ", 1)[1].strip()
    return command


def _shell_welcome() -> str:
    return "\n".join(
        [
            "Interactive shell active.",
            "Type `help` for shortcuts and examples, or `exit` to leave.",
            "",
        ]
    )


def _shell_help() -> str:
    return "\n".join(
        [
            "Patchrail shell",
            "Shortcuts:",
            "  help, /help          Show this help",
            "  exit, quit, /exit    Leave the shell",
            "  doctor, /doctor      Show readiness summary",
            "  start, /start        Redraw the home screen once",
            "  list tasks, /tasks   List stored tasks",
            "Examples:",
            '  task create --title "First task" --description "Describe the work"',
            "  plan --task-id <task_id> --auto",
            "  status --task-id <task_id>",
        ]
    )


def _render_args(command: str) -> Any:
    return SimpleNamespace(command=command)


def _isatty(stream: TextIO) -> bool:
    isatty = getattr(stream, "isatty", None)
    if not callable(isatty):
        return False
    return bool(isatty())


def _write_block(stream: TextIO, text: str) -> None:
    stream.write(text.rstrip() + "\n\n")
    stream.flush()


def _write_line(stream: TextIO, text: str) -> None:
    stream.write(text + "\n")
    stream.flush()
