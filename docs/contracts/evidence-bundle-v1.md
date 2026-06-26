# Evidence Bundle v1

Patchrail Evidence Bundle v1 is the local manifest contract for post-run evidence captured after executor execution and before review.

Schema version: `patchrail.evidence_bundle.v1`

## Boundary

- Patchrail owns the stored artifact bundle record and manifest metadata.
- Evidence bundles do not own canonical lifecycle state.
- The canonical lifecycle remains `Task -> Plan -> Run -> ReviewResult -> ApprovalRecord`.
- A run stores the artifact bundle identity, but the bundle remains a queryable evidence record under Patchrail-owned storage.
- Runner adapters may provide files or structured trace data, but they do not own approval meaning, review verdicts, or canonical run state.

## Timing

Evidence is collected after the executor returns and before review begins.

Phase: `after_executor_run_before_review`

## Required Logical Kinds

Every v1 bundle includes manifest entries for:

- `execution_summary`
- `diff_summary`
- `runner_stdout`
- `runner_stderr`
- `runner_invocation`

## Optional Logical Kinds

The v1 bundle may include:

- `runner_trace`
- `runner_artifact`

## Bundle Fields

Each stored artifact bundle includes:

- `run_id`
- `created_at`
- `schema_version`
- `files`
- `summary`
- `artifacts`

## Artifact Manifest Fields

Each artifact manifest entry includes:

- `path`
- `logical_kind`
- `media_type`
- `collection_status`
- `sha256`
- `size_bytes`

## Read Visibility

- `patchrail --json status --task-id <task_id>` returns `latest_artifact_bundle.schema_version`.
- `patchrail --json artifacts --run-id <run_id>` returns `artifact_bundle.schema_version`.
- `patchrail --json list artifact-bundles` returns the same schema marker for historical bundle records.
- `patchrail list artifact-bundles --logical-kind <kind>` remains a Patchrail-owned read-side query over manifest metadata.

## Local Rules

- The stored digest for each artifact covers that artifact's persisted bytes.
- The invocation record is required so reviewers can reconstruct the supervised runner call.
- Runner-local files collected from `.patchrail/workspaces/<run_id>/artifacts/` are copied into `.patchrail/artifacts/<run_id>/runner-artifacts/` before manifest persistence. The runner writes exchange files; Patchrail owns the canonical evidence copy.
- The bundle manifest is immutable once persisted for a completed run.
- Existing bundles without an explicit `schema_version` are interpreted as `patchrail.evidence_bundle.v1` for backward-compatible local reads.
