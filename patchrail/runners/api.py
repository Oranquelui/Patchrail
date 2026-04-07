from __future__ import annotations

from pathlib import Path

from patchrail.models.entities import Plan, Task
from patchrail.models.roles import RoleCandidate
from patchrail.providers.executor_api import execute_api_candidate
from patchrail.runners.base import Runner, RunnerResult


class ProviderApiRunner(Runner):
    def __init__(self, candidate: RoleCandidate, runner_name: str) -> None:
        self._candidate = candidate
        self.name = runner_name
        self.mode = "api"
        self.command = f"provider-api:{candidate.provider.value}"

    def run(self, task: Task, plan: Plan, workspace_path: Path, run_id: str) -> RunnerResult:
        return execute_api_candidate(self._candidate, task, plan)


def build_api_runner(candidate: RoleCandidate, runner_name: str) -> Runner:
    return ProviderApiRunner(candidate=candidate, runner_name=runner_name)
