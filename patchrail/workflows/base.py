from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from patchrail.models.entities import ArtifactBundle, Plan, PlanningBrief, ReviewVerdict, Run, Task
from patchrail.models.roles import RoleCandidate


@dataclass(slots=True)
class PlanWorkflowResult:
    summary: str
    steps: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReviewWorkflowResult:
    verdict: ReviewVerdict
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowEngine(ABC):
    backend_name: str

    @abstractmethod
    def generate_plan(
        self,
        candidate: RoleCandidate,
        task: Task,
        briefs: list[PlanningBrief] | None = None,
    ) -> PlanWorkflowResult:
        raise NotImplementedError

    @abstractmethod
    def generate_review(
        self,
        candidate: RoleCandidate,
        task: Task,
        plan: Plan,
        run: Run,
        bundle: ArtifactBundle,
    ) -> ReviewWorkflowResult:
        raise NotImplementedError
