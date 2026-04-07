from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from patchrail.models.entities import CostMetrics, Plan, Task


@dataclass(slots=True)
class RunnerResult:
    stdout: str
    stderr: str
    execution_summary: str
    diff_summary: str
    cost_metrics: CostMetrics
    exit_code: int


class Runner(ABC):
    name: str
    mode: str
    command: str | None

    @abstractmethod
    def run(self, task: Task, plan: Plan, workspace_path: Path, run_id: str) -> RunnerResult:
        raise NotImplementedError
