from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"


class Provider(StrEnum):
    CODEX = "codex"
    CLAUDE = "claude"
    GROK = "grok"


class AccessMode(StrEnum):
    API = "api"
    SUBSCRIPTION = "subscription"


@dataclass(slots=True)
class CapabilityProfile:
    supports_planning: bool = False
    supports_review: bool = False
    supports_execution: bool = False
    supports_json_output: bool = False
    supports_noninteractive: bool = False

    @classmethod
    def from_capabilities(cls, capabilities: list[str]) -> CapabilityProfile:
        values = set(capabilities)
        return cls(
            supports_planning="planning" in values,
            supports_review="review" in values,
            supports_execution="execution" in values,
            supports_json_output="json_output" in values,
            supports_noninteractive="noninteractive" in values,
        )

    def to_capabilities(self) -> list[str]:
        capabilities: list[str] = []
        if self.supports_planning:
            capabilities.append("planning")
        if self.supports_review:
            capabilities.append("review")
        if self.supports_execution:
            capabilities.append("execution")
        if self.supports_json_output:
            capabilities.append("json_output")
        if self.supports_noninteractive:
            capabilities.append("noninteractive")
        return capabilities


@dataclass(slots=True)
class RoleCandidate:
    name: str
    role: Role
    provider: Provider
    access_mode: AccessMode
    capability_profile: CapabilityProfile
    command: str | None = None
    api_key_env: str | None = None
    endpoint_env: str | None = None
    simulation: bool = False

    @classmethod
    def from_dict(cls, role: Role, payload: dict[str, Any]) -> RoleCandidate:
        return cls(
            name=payload["name"],
            role=role,
            provider=Provider(payload["provider"]),
            access_mode=AccessMode(payload["access_mode"]),
            capability_profile=CapabilityProfile.from_capabilities(list(payload.get("capabilities", []))),
            command=payload.get("command"),
            api_key_env=payload.get("api_key_env"),
            endpoint_env=payload.get("endpoint_env"),
            simulation=bool(payload.get("simulation", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "provider": self.provider.value,
            "access_mode": self.access_mode.value,
            "capabilities": self.capability_profile.to_capabilities(),
            "command": self.command,
            "api_key_env": self.api_key_env,
            "endpoint_env": self.endpoint_env,
            "simulation": self.simulation,
        }


@dataclass(slots=True)
class RolePolicy:
    role: Role
    candidates: list[RoleCandidate] = field(default_factory=list)

    @classmethod
    def from_dict(cls, role: Role, payload: dict[str, Any]) -> RolePolicy:
        return cls(
            role=role,
            candidates=[RoleCandidate.from_dict(role, item) for item in payload.get("candidates", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return {"candidates": [candidate.to_dict() for candidate in self.candidates]}


@dataclass(slots=True)
class RolePolicySet:
    roles: dict[Role, RolePolicy]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RolePolicySet:
        roles_payload = payload.get("roles", {})
        return cls(
            roles={
                Role(role_name): RolePolicy.from_dict(Role(role_name), role_payload)
                for role_name, role_payload in roles_payload.items()
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {"roles": {role.value: policy.to_dict() for role, policy in self.roles.items()}}

    def get_policy(self, role: Role) -> RolePolicy:
        return self.roles[role]


@dataclass(slots=True)
class PreflightCheck:
    name: str
    passed: bool
    detail: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PreflightCheck:
        return cls(**payload)


@dataclass(slots=True)
class PreflightResult:
    candidate_name: str
    role: Role
    provider: Provider
    access_mode: AccessMode
    ready: bool
    checks: list[PreflightCheck] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PreflightResult:
        return cls(
            candidate_name=payload["candidate_name"],
            role=Role(payload["role"]),
            provider=Provider(payload["provider"]),
            access_mode=AccessMode(payload["access_mode"]),
            ready=bool(payload["ready"]),
            checks=[PreflightCheck.from_dict(item) for item in payload.get("checks", [])],
        )


@dataclass(slots=True)
class FallbackEvent:
    role: Role
    attempted_candidate: str
    selected_candidate: str
    reason: str
    requires_additional_approval: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FallbackEvent:
        return cls(
            role=Role(payload["role"]),
            attempted_candidate=payload["attempted_candidate"],
            selected_candidate=payload["selected_candidate"],
            reason=payload["reason"],
            requires_additional_approval=bool(payload["requires_additional_approval"]),
        )


@dataclass(slots=True)
class ResolvedAssignment:
    role: Role
    candidate_name: str
    provider: Provider
    access_mode: AccessMode
    command: str | None
    requires_additional_approval: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResolvedAssignment:
        return cls(
            role=Role(payload["role"]),
            candidate_name=payload["candidate_name"],
            provider=Provider(payload["provider"]),
            access_mode=AccessMode(payload["access_mode"]),
            command=payload.get("command"),
            requires_additional_approval=bool(payload.get("requires_additional_approval", False)),
        )
