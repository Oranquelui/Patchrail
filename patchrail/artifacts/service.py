from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
from pathlib import Path
from typing import Any

from patchrail.core.layers import EVIDENCE_BUNDLE_CONTRACT
from patchrail.core.ids import utc_now
from patchrail.models.entities import ArtifactBundle, ArtifactFile
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
        runner_trace: dict[str, Any] | None = None,
        runner_artifact_dir: Path | None = None,
    ) -> ArtifactBundle:
        artifact_dir = self.store.artifact_dir(run_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        stdout_path = artifact_dir / "stdout.log"
        stderr_path = artifact_dir / "stderr.log"
        execution_path = artifact_dir / "execution-summary.md"
        diff_path = artifact_dir / "diff-summary.md"
        invocation_path = artifact_dir / "invocation.json"
        trace_path = artifact_dir / "trace.json"

        stdout_path.write_text(stdout)
        stderr_path.write_text(stderr)
        execution_path.write_text(execution_summary)
        diff_path.write_text(diff_summary)
        invocation_path.write_text(json.dumps(invocation, indent=2, sort_keys=True) + "\n")
        if runner_trace is not None:
            trace_path.write_text(json.dumps(runner_trace, indent=2, sort_keys=True) + "\n")

        files = {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "execution_summary": str(execution_path),
            "diff_summary": str(diff_path),
            "invocation": str(invocation_path),
            "bundle": str(artifact_dir / "bundle.json"),
        }
        artifacts = {
            "stdout": self._artifact_file(stdout_path, logical_kind="runner_stdout", media_type="text/plain"),
            "stderr": self._artifact_file(stderr_path, logical_kind="runner_stderr", media_type="text/plain"),
            "execution_summary": self._artifact_file(
                execution_path,
                logical_kind="execution_summary",
                media_type="text/markdown",
            ),
            "diff_summary": self._artifact_file(
                diff_path,
                logical_kind="diff_summary",
                media_type="text/markdown",
            ),
            "invocation": self._artifact_file(
                invocation_path,
                logical_kind="runner_invocation",
                media_type="application/json",
            ),
        }
        if runner_trace is not None:
            files["trace"] = str(trace_path)
            artifacts["trace"] = self._artifact_file(
                trace_path,
                logical_kind="runner_trace",
                media_type="application/json",
            )
        self._collect_runner_artifacts(
            runner_artifact_dir=runner_artifact_dir,
            canonical_artifact_dir=artifact_dir,
            files=files,
            artifacts=artifacts,
        )

        bundle = ArtifactBundle(
            run_id=run_id,
            created_at=utc_now(),
            files=files,
            schema_version=EVIDENCE_BUNDLE_CONTRACT.schema_version,
            artifacts=artifacts,
            summary=execution_summary,
        )
        self.store.save_artifact_bundle(bundle)
        return bundle

    def get_bundle(self, run_id: str) -> ArtifactBundle:
        return self.store.load_artifact_bundle(run_id)

    def get_stdout(self, run_id: str) -> str:
        return self.store.read_stdout_log(run_id)

    def _collect_runner_artifacts(
        self,
        runner_artifact_dir: Path | None,
        canonical_artifact_dir: Path,
        files: dict[str, str],
        artifacts: dict[str, ArtifactFile],
    ) -> None:
        if runner_artifact_dir is None or not runner_artifact_dir.exists():
            return

        canonical_runner_dir = canonical_artifact_dir / "runner-artifacts"
        for source_path in sorted(
            path for path in runner_artifact_dir.rglob("*") if path.is_file() and not path.is_symlink()
        ):
            relative_path = source_path.relative_to(runner_artifact_dir)
            destination_path = canonical_runner_dir / relative_path
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
            manifest_key = f"runner_artifact:{relative_path.as_posix()}"
            files[manifest_key] = str(destination_path)
            artifacts[manifest_key] = self._artifact_file(
                destination_path,
                logical_kind="runner_artifact",
                media_type=self._media_type(destination_path),
            )

    def _artifact_file(self, path: Path, logical_kind: str, media_type: str) -> ArtifactFile:
        payload = path.read_bytes()
        return ArtifactFile(
            path=str(path),
            logical_kind=logical_kind,
            media_type=media_type,
            collection_status="collected",
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
        )

    def _media_type(self, path: Path) -> str:
        if path.suffix == ".json":
            return "application/json"
        media_type, _encoding = mimetypes.guess_type(path.name)
        return media_type or "application/octet-stream"
