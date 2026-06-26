# Brief Schema v1

Patchrail Brief Schema v1 is the local companion-artifact contract for planning briefs created before the canonical plan.

Schema version: `patchrail.brief_schema.v1`

## Boundary

- Patchrail owns the stored brief records and their SHA-256 digests.
- Briefs do not own canonical lifecycle state.
- The canonical lifecycle remains `Task -> Plan -> Run -> ReviewResult -> ApprovalRecord`.
- A plan snapshots references to the task's current briefs, including the schema version used by each referenced companion artifact.
- The stored brief record remains the source for full content.

## Sequence

Briefs are ordered and interpreted as:

1. `future`: prediction layer.
2. `ontology`: reality-boundary layer.
3. `product`: post-implementation acceptance layer.

## Record Fields

Each stored brief record includes:

- `id`
- `task_id`
- `kind`
- `schema_version`
- `source_path`
- `storage_path`
- `content`
- `sha256`
- `created_at`
- `attached_plan_id`

## Plan Reference Fields

Each canonical plan snapshot stores a compact brief reference with:

- `id`
- `kind`
- `schema_version`
- `source_path`
- `storage_path`
- `sha256`
- `created_at`

## Read Visibility

- `patchrail brief validate --task-id <task_id>` reports the required v1 sequence, present kinds, and missing kinds without mutating task state.
- `patchrail brief show --brief-id <brief_id>` displays `schema_version` in human-readable output.
- `patchrail --json brief show --brief-id <brief_id>` returns `brief.schema_version`.
- `patchrail --json brief list --task-id <task_id>` returns `schema_version` for each brief record.
- `patchrail --json plan ...` and `patchrail --json status --task-id <task_id>` return `schema_version` for each `plan.planning_briefs` reference.

## Local Rules

- Briefs must be created before the canonical plan.
- Only one pending brief per kind is allowed for a task.
- Brief source content is copied into Patchrail-owned storage.
- The stored digest covers the brief content exactly as persisted.
- Generated project scaffolds include the schema version so operators can see which contract they are filling in.
- Validation is advisory in v1; it surfaces readiness and missing kinds but does not create a second lifecycle gate.
