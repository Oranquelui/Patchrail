from __future__ import annotations

import os
import shlex
import shutil

from patchrail.models.roles import AccessMode, PreflightCheck, PreflightResult, RoleCandidate


def perform_preflight(candidate: RoleCandidate) -> PreflightResult:
    checks: list[PreflightCheck] = []

    if candidate.access_mode == AccessMode.API:
        credential_ok = bool(candidate.api_key_env and os.getenv(candidate.api_key_env))
        endpoint_ok = bool(candidate.endpoint_env and os.getenv(candidate.endpoint_env))
        checks.append(
            PreflightCheck(
                name="credential_present",
                passed=credential_ok,
                detail=candidate.api_key_env or "missing_api_key_env",
            )
        )
        checks.append(
            PreflightCheck(
                name="endpoint_configured",
                passed=endpoint_ok,
                detail=candidate.endpoint_env or "missing_endpoint_env",
            )
        )
    else:
        checks.append(PreflightCheck(name="cli_present", passed=_command_exists(candidate.command), detail=candidate.command or ""))
        checks.append(
            PreflightCheck(
                name="login_ok",
                passed=candidate.simulation or _subscription_flag(candidate, "LOGIN"),
                detail="simulation" if candidate.simulation else "env",
            )
        )
        checks.append(
            PreflightCheck(
                name="entitlement_ok",
                passed=candidate.simulation or _subscription_flag(candidate, "ENTITLEMENT"),
                detail="simulation" if candidate.simulation else "env",
            )
        )
        checks.append(
            PreflightCheck(
                name="noninteractive_ok",
                passed=candidate.simulation or _subscription_flag(candidate, "NONINTERACTIVE"),
                detail="simulation" if candidate.simulation else "env",
            )
        )

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


def _subscription_flag(candidate: RoleCandidate, suffix: str) -> bool:
    env_name = f"PATCHRAIL_{candidate.provider.value.upper()}_SUBSCRIPTION_{suffix}"
    return os.getenv(env_name) == "1"
