from __future__ import annotations

from dataclasses import dataclass

from patchrail.models.roles import (
    AccessMode,
    FallbackEvent,
    PreflightResult,
    Provider,
    ResolvedAssignment,
    Role,
    RoleCandidate,
    RolePolicySet,
)

from patchrail.core.preflight import perform_preflight


@dataclass(slots=True)
class AssignmentResolution:
    role: Role
    results: list[PreflightResult]
    selected_assignment: ResolvedAssignment | None
    selected_candidate: RoleCandidate | None
    fallback_event: FallbackEvent | None


def resolve_role_assignment(
    policy_set: RolePolicySet,
    role: Role,
    provider_filter: Provider | None = None,
    access_mode_filter: AccessMode | None = None,
) -> AssignmentResolution:
    policy = policy_set.get_policy(role)
    candidates = [
        candidate
        for candidate in policy.candidates
        if (provider_filter is None or candidate.provider == provider_filter)
        and (access_mode_filter is None or candidate.access_mode == access_mode_filter)
    ]
    results = [perform_preflight(candidate) for candidate in candidates]
    if not candidates:
        return AssignmentResolution(
            role=role,
            results=[],
            selected_assignment=None,
            selected_candidate=None,
            fallback_event=None,
        )

    first_candidate = candidates[0]
    for candidate, result in zip(candidates, results, strict=False):
        if not result.ready:
            continue
        requires_approval = (
            candidate.provider != first_candidate.provider or candidate.access_mode != first_candidate.access_mode
        ) and candidate.name != first_candidate.name
        fallback_event = None
        if candidate.name != first_candidate.name:
            fallback_event = FallbackEvent(
                role=role,
                attempted_candidate=first_candidate.name,
                selected_candidate=candidate.name,
                reason="primary candidate blocked during preflight",
                requires_additional_approval=requires_approval,
            )
        assignment = ResolvedAssignment(
            role=role,
            candidate_name=candidate.name,
            provider=candidate.provider,
            access_mode=candidate.access_mode,
            model=candidate.model,
            command=None if candidate.access_mode == AccessMode.API else candidate.command,
            requires_additional_approval=requires_approval,
        )
        return AssignmentResolution(
            role=role,
            results=results,
            selected_assignment=assignment,
            selected_candidate=candidate,
            fallback_event=fallback_event,
        )
    return AssignmentResolution(
        role=role,
        results=results,
        selected_assignment=None,
        selected_candidate=None,
        fallback_event=None,
    )
