from __future__ import annotations

import json
from typing import Any

from patchrail.core.ids import utc_now
from patchrail.models.entities import ArtifactBundle
from patchrail.storage.filesystem import FilesystemStore


class ArtifactService:
    def __init__(self, store: FilesystemStore) -> None:
        self.store = store

    def create_bundle(
        self,
        run_id: str,
        execution_summary: str,
        diff_summary: str,
        stdout: str,
        stderr: str,
        invocation: dict[str, Any],
    ) -> ArtifactBundle:
        artifact_dir = self.store.artifact_dir(run_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        stdout_path = artifact_dir / "stdout.log"
        stderr_path = artifact_dir / "stderr.log"
        execution_path = artifact_dir / "execution-summary.md"
        diff_path = artifact_dir / "diff-summary.md"
        invocation_path = artifact_dir / "invocation.json"

        stdout_path.write_text(stdout)
        stderr_path.write_text(stderr)
        execution_path.write_text(execution_summary)
        diff_path.write_text(diff_summary)
        invocation_path.write_text(json.dumps(invocation, indent=2, sort_keys=True) + "\n")

        bundle = ArtifactBundle(
            run_id=run_id,
            created_at=utc_now(),
            files={
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
                "execution_summary": str(execution_path),
                "diff_summary": str(diff_path),
                "invocation": str(invocation_path),
                "bundle": str(artifact_dir / "bundle.json"),
            },
            summary=execution_summary,
        )
        self.store.save_artifact_bundle(bundle)
        return bundle

    def get_bundle(self, run_id: str) -> ArtifactBundle:
        return self.store.load_artifact_bundle(run_id)

    def get_stdout(self, run_id: str) -> str:
        return self.store.read_stdout_log(run_id)
