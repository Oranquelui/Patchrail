from __future__ import annotations

import json
import sys
from pathlib import Path

from patchrail.models.roles import AccessMode, Provider, Role, RoleCandidate, RolePolicy, RolePolicySet


class ConfigStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.config_dir = self.root / "config"
        self.config_path = self.config_dir / "role-policy.json"
        self.workflow_path = self.config_dir / "workflow-backend.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def init_default(self, preset: str = "local", workflow_backend: str = "local") -> RolePolicySet:
        policy = self._policy_for_preset(preset)
        self.write_policy(policy)
        self.write_workflow_backend(workflow_backend)
        return policy

    def load_policy(self) -> RolePolicySet:
        if not self.config_path.exists():
            return self.init_default()
        return RolePolicySet.from_dict(json.loads(self.config_path.read_text()))

    def load_workflow_backend(self) -> str:
        if not self.workflow_path.exists():
            return "local"
        payload = json.loads(self.workflow_path.read_text())
        backend = payload.get("workflow_backend", "local")
        return self._validated_workflow_backend(backend)

    def write_policy(self, policy: RolePolicySet) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(policy.to_dict(), indent=2, sort_keys=True) + "\n")

    def write_workflow_backend(self, workflow_backend: str) -> None:
        backend = self._validated_workflow_backend(workflow_backend)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.workflow_path.write_text(json.dumps({"workflow_backend": backend}, indent=2, sort_keys=True) + "\n")

    def _validated_workflow_backend(self, workflow_backend: str) -> str:
        backend = str(workflow_backend).strip().lower()
        if backend not in {"local", "langgraph"}:
            raise ValueError(f"Unsupported workflow backend: {workflow_backend}")
        return backend

    def _policy_for_preset(self, preset: str) -> RolePolicySet:
        if preset == "local":
            return self._local_policy()
        if preset == "real":
            return self._real_policy()
        raise ValueError(f"Unsupported preset: {preset}")

    def _local_policy(self) -> RolePolicySet:
        python_bin = sys.executable
        harness_command = f"{python_bin} -m patchrail.runners.local_harness"

        planner = RolePolicy(
            role=Role.PLANNER,
            candidates=[
                RoleCandidate(
                    name="claude_subscription_planner",
                    role=Role.PLANNER,
                    provider=Provider.CLAUDE,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.PLANNER,
                        {
                            "name": "temp",
                            "provider": "claude",
                            "access_mode": "subscription",
                            "capabilities": ["planning", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    simulation=True,
                ),
                RoleCandidate(
                    name="codex_api_planner",
                    role=Role.PLANNER,
                    provider=Provider.CODEX,
                    access_mode=AccessMode.API,
                    model="gpt-5.2-codex",
                    capability_profile=RoleCandidate.from_dict(
                        Role.PLANNER,
                        {
                            "name": "temp",
                            "provider": "codex",
                            "access_mode": "api",
                            "capabilities": ["planning", "json_output"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    api_key_env="PATCHRAIL_CODEX_API_KEY",
                    endpoint_env="PATCHRAIL_CODEX_API_BASE",
                ),
            ],
        )
        reviewer = RolePolicy(
            role=Role.REVIEWER,
            candidates=[
                RoleCandidate(
                    name="codex_subscription_reviewer",
                    role=Role.REVIEWER,
                    provider=Provider.CODEX,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.REVIEWER,
                        {
                            "name": "temp",
                            "provider": "codex",
                            "access_mode": "subscription",
                            "capabilities": ["review", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    simulation=True,
                ),
                RoleCandidate(
                    name="claude_api_reviewer",
                    role=Role.REVIEWER,
                    provider=Provider.CLAUDE,
                    access_mode=AccessMode.API,
                    model="claude-sonnet-4-20250514",
                    capability_profile=RoleCandidate.from_dict(
                        Role.REVIEWER,
                        {
                            "name": "temp",
                            "provider": "claude",
                            "access_mode": "api",
                            "capabilities": ["review", "json_output"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    api_key_env="PATCHRAIL_CLAUDE_API_KEY",
                    endpoint_env="PATCHRAIL_CLAUDE_API_BASE",
                ),
            ],
        )
        executor = RolePolicy(
            role=Role.EXECUTOR,
            candidates=[
                RoleCandidate(
                    name="claude_subscription_executor",
                    role=Role.EXECUTOR,
                    provider=Provider.CLAUDE,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.EXECUTOR,
                        {
                            "name": "temp",
                            "provider": "claude",
                            "access_mode": "subscription",
                            "capabilities": ["execution", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    simulation=True,
                ),
                RoleCandidate(
                    name="codex_subscription_executor",
                    role=Role.EXECUTOR,
                    provider=Provider.CODEX,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.EXECUTOR,
                        {
                            "name": "temp",
                            "provider": "codex",
                            "access_mode": "subscription",
                            "capabilities": ["execution", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    simulation=True,
                ),
                RoleCandidate(
                    name="grok_api_executor",
                    role=Role.EXECUTOR,
                    provider=Provider.GROK,
                    access_mode=AccessMode.API,
                    model="grok-4-0709",
                    capability_profile=RoleCandidate.from_dict(
                        Role.EXECUTOR,
                        {
                            "name": "temp",
                            "provider": "grok",
                            "access_mode": "api",
                            "capabilities": ["execution", "json_output"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    simulation=True,
                    api_key_env="PATCHRAIL_GROK_API_KEY",
                    endpoint_env="PATCHRAIL_GROK_API_BASE",
                ),
            ],
        )
        return RolePolicySet(roles={Role.PLANNER: planner, Role.REVIEWER: reviewer, Role.EXECUTOR: executor})

    def _real_policy(self) -> RolePolicySet:
        python_bin = sys.executable
        harness_command = f"{python_bin} -m patchrail.runners.local_harness"

        planner = RolePolicy(
            role=Role.PLANNER,
            candidates=[
                RoleCandidate(
                    name="claude_subscription_planner",
                    role=Role.PLANNER,
                    provider=Provider.CLAUDE,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.PLANNER,
                        {
                            "name": "temp",
                            "provider": "claude",
                            "access_mode": "subscription",
                            "capabilities": ["planning", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    cli_command="claude",
                ),
                RoleCandidate(
                    name="codex_api_planner",
                    role=Role.PLANNER,
                    provider=Provider.CODEX,
                    access_mode=AccessMode.API,
                    model="gpt-5.2-codex",
                    capability_profile=RoleCandidate.from_dict(
                        Role.PLANNER,
                        {
                            "name": "temp",
                            "provider": "codex",
                            "access_mode": "api",
                            "capabilities": ["planning", "json_output"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    api_key_env="OPENAI_API_KEY",
                ),
            ],
        )
        reviewer = RolePolicy(
            role=Role.REVIEWER,
            candidates=[
                RoleCandidate(
                    name="codex_subscription_reviewer",
                    role=Role.REVIEWER,
                    provider=Provider.CODEX,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.REVIEWER,
                        {
                            "name": "temp",
                            "provider": "codex",
                            "access_mode": "subscription",
                            "capabilities": ["review", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    cli_command="codex",
                ),
                RoleCandidate(
                    name="claude_api_reviewer",
                    role=Role.REVIEWER,
                    provider=Provider.CLAUDE,
                    access_mode=AccessMode.API,
                    model="claude-sonnet-4-20250514",
                    capability_profile=RoleCandidate.from_dict(
                        Role.REVIEWER,
                        {
                            "name": "temp",
                            "provider": "claude",
                            "access_mode": "api",
                            "capabilities": ["review", "json_output"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    api_key_env="ANTHROPIC_API_KEY",
                ),
            ],
        )
        executor = RolePolicy(
            role=Role.EXECUTOR,
            candidates=[
                RoleCandidate(
                    name="grok_api_executor",
                    role=Role.EXECUTOR,
                    provider=Provider.GROK,
                    access_mode=AccessMode.API,
                    model="grok-4-0709",
                    capability_profile=RoleCandidate.from_dict(
                        Role.EXECUTOR,
                        {
                            "name": "temp",
                            "provider": "grok",
                            "access_mode": "api",
                            "capabilities": ["execution", "json_output"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    api_key_env="XAI_API_KEY",
                ),
                RoleCandidate(
                    name="claude_subscription_executor",
                    role=Role.EXECUTOR,
                    provider=Provider.CLAUDE,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.EXECUTOR,
                        {
                            "name": "temp",
                            "provider": "claude",
                            "access_mode": "subscription",
                            "capabilities": ["execution", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    cli_command="claude",
                ),
                RoleCandidate(
                    name="codex_subscription_executor",
                    role=Role.EXECUTOR,
                    provider=Provider.CODEX,
                    access_mode=AccessMode.SUBSCRIPTION,
                    capability_profile=RoleCandidate.from_dict(
                        Role.EXECUTOR,
                        {
                            "name": "temp",
                            "provider": "codex",
                            "access_mode": "subscription",
                            "capabilities": ["execution", "json_output", "noninteractive"],
                        },
                    ).capability_profile,
                    command=harness_command,
                    cli_command="codex",
                ),
            ],
        )
        return RolePolicySet(roles={Role.PLANNER: planner, Role.REVIEWER: reviewer, Role.EXECUTOR: executor})
