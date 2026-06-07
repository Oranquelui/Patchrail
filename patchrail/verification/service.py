from __future__ import annotations

import subprocess
import time
from pathlib import Path

from patchrail.core.ids import generate_id, utc_now
from patchrail.models.entities import VerificationRecord, VerificationStatus
from patchrail.storage.filesystem import FilesystemStore


class VerificationService:
    def __init__(self, store: FilesystemStore) -> None:
        self.store = store

    def run_verification(self, run_id: str, command: str, cwd: Path | None = None) -> VerificationRecord:
        run = self.store.load_run(run_id)
        verification_id = generate_id("verification")
        output_dir = self.store.verification_output_dir(verification_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = output_dir / "stdout.log"
        stderr_path = output_dir / "stderr.log"
        working_dir = cwd or Path.cwd()

        started = time.perf_counter()
        completed = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        elapsed_seconds = time.perf_counter() - started

        stdout_path.write_text(completed.stdout)
        stderr_path.write_text(completed.stderr)
        verification = VerificationRecord(
            id=verification_id,
            task_id=run.task_id,
            run_id=run.id,
            command=command,
            cwd=str(working_dir),
            exit_code=completed.returncode,
            status=VerificationStatus.PASSED if completed.returncode == 0 else VerificationStatus.FAILED,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            elapsed_seconds=elapsed_seconds,
            created_at=utc_now(),
        )
        self.store.save_verification(verification)
        return verification

    def list_verifications(
        self,
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> list[VerificationRecord]:
        verifications = self.store.list_verifications()
        if task_id is not None:
            verifications = [verification for verification in verifications if verification.task_id == task_id]
        if run_id is not None:
            verifications = [verification for verification in verifications if verification.run_id == run_id]
        return verifications
