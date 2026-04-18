from __future__ import annotations

import importlib
import os

from patchrail.core.exceptions import PatchrailError
from patchrail.storage.filesystem import FilesystemStore
from patchrail.workflows.base import PlanWorkflowResult, ReviewWorkflowResult, WorkflowEngine
from patchrail.workflows.local import LocalWorkflowEngine

__all__ = [
    "PlanWorkflowResult",
    "ReviewWorkflowResult",
    "WorkflowEngine",
    "build_workflow_engine",
]


def build_workflow_engine(store: FilesystemStore) -> WorkflowEngine:
    del store
    backend_name = os.getenv("PATCHRAIL_WORKFLOW_BACKEND", "local").strip().lower()
    if not backend_name or backend_name == "local":
        return LocalWorkflowEngine()
    if backend_name == "langgraph":
        try:
            module = importlib.import_module("patchrail.workflows.langgraph_backend")
        except ImportError as exc:
            raise PatchrailError(
                "LangGraph workflow backend requires the optional 'langgraph' dependency. "
                "Install it or unset PATCHRAIL_WORKFLOW_BACKEND."
            ) from exc
        return module.LangGraphWorkflowEngine()
    raise PatchrailError(
        f"Unknown workflow backend '{backend_name}'. Use 'local' or 'langgraph'."
    )
