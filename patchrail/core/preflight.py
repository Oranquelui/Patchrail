from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess

from patchrail.models.roles import AccessMode, PreflightCheck, PreflightResult, Provider, RoleCandidate


def perform_preflight(candidate: RoleCandidate) -> PreflightResult:
    checks: list[PreflightCheck] = []

    if candidate.access_mode == AccessMode.API:
        credential_ok = candidate.simulation or bool(candidate.api_key_env and os.getenv(candidate.api_key_env))
        endpoint_ok = candidate.simulation or (
            True if candidate.endpoint_env is None else bool(os.getenv(candidate.endpoint_env))
        )
        checks.append(
            PreflightCheck(
                name="credential_present",
                passed=credential_ok,
                detail="simulation" if candidate.simulation else (candidate.api_key_env or "missing_api_key_env"),
            )
        )
        checks.append(
            PreflightCheck(
                name="endpoint_configured",
                passed=endpoint_ok,
                detail="simulation" if candidate.simulation else (candidate.endpoint_env or "default_endpoint"),
            )
        )
    else:
        cli_target = candidate.cli_command or candidate.command
        cli_ok = candidate.simulation or _command_exists(cli_target)
        checks.append(PreflightCheck(name="cli_present", passed=cli_ok, detail=cli_target or ""))
        checks.extend(_subscription_checks(candidate, cli_ok))

    return PreflightResult(
        candidate_name=candidate.name,
        role=candidate.role,
        provider=candidate.provider,
        access_mode=candidate.access_mode,
        ready=all(check.passed for check in checks),
        checks=checks,
    )


def _command_exists(command: str | None) -> bool:
    if not command:
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if not parts:
        return False
    executable = parts[0]
    if os.path.isabs(executable):
        return os.path.exists(executable)
    return shutil.which(executable) is not None


def _subscription_checks(candidate: RoleCandidate, cli_ok: bool) -> list[PreflightCheck]:
    if candidate.simulation:
        return [
            PreflightCheck(name="login_ok", passed=True, detail="simulation"),
            PreflightCheck(name="entitlement_ok", passed=True, detail="simulation"),
            PreflightCheck(name="noninteractive_ok", passed=True, detail="simulation"),
        ]
    if not cli_ok:
        return [
            PreflightCheck(name="login_ok", passed=False, detail="cli_missing"),
            PreflightCheck(name="entitlement_ok", passed=False, detail="cli_missing"),
            PreflightCheck(name="noninteractive_ok", passed=False, detail="cli_missing"),
        ]
    if candidate.provider == Provider.CODEX:
        return _codex_subscription_checks(candidate)
    if candidate.provider == Provider.CLAUDE:
        return _claude_subscription_checks(candidate)
    return [
        PreflightCheck(name="login_ok", passed=False, detail="unsupported_provider"),
        PreflightCheck(name="entitlement_ok", passed=False, detail="unsupported_provider"),
        PreflightCheck(name="noninteractive_ok", passed=False, detail="unsupported_provider"),
    ]


def _codex_subscription_checks(candidate: RoleCandidate) -> list[PreflightCheck]:
    command = [candidate.cli_command or "codex", "login", "status"]
    returncode, stdout, stderr = _run_status_command(command)
    detail = _status_detail(returncode, stdout, stderr)
    logged_in = returncode == 0 and "logged in" in detail.lower()
    return [
        PreflightCheck(name="login_ok", passed=logged_in, detail=detail),
        PreflightCheck(name="entitlement_ok", passed=logged_in, detail=detail),
        PreflightCheck(name="noninteractive_ok", passed=returncode == 0, detail=detail),
    ]


def _claude_subscription_checks(candidate: RoleCandidate) -> list[PreflightCheck]:
    command = [candidate.cli_command or "claude", "auth", "status"]
    returncode, stdout, stderr = _run_status_command(command)
    detail = _status_detail(returncode, stdout, stderr)
    payload = _parse_json(stdout)
    logged_in = returncode == 0 and isinstance(payload, dict) and bool(payload.get("loggedIn"))
    subscription_type = ""
    if isinstance(payload, dict):
        subscription_type = str(payload.get("subscriptionType") or "").strip().lower()
    entitled = logged_in and subscription_type not in {"", "none", "unknown"}
    noninteractive = returncode == 0 and isinstance(payload, dict)
    detail_value = subscription_type or detail
    return [
        PreflightCheck(name="login_ok", passed=logged_in, detail=detail_value),
        PreflightCheck(name="entitlement_ok", passed=entitled, detail=detail_value),
        PreflightCheck(name="noninteractive_ok", passed=noninteractive, detail=detail_value),
    ]
def _run_status_command(command: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return (1, "", str(exc))
    return (result.returncode, result.stdout.strip(), result.stderr.strip())


def _status_detail(returncode: int, stdout: str, stderr: str) -> str:
    for value in (stdout, stderr):
        if value:
            return value.strip()
    return f"exit={returncode}"


def _parse_json(raw: str) -> dict[str, object] | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None
