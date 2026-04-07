from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class HookEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)


class HookRegistry:
    """Future-facing hook seam. The MVP stores no subscribers and performs no side effects."""

    def dispatch(self, event: HookEvent) -> None:
        _ = event
