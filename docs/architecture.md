# Patchrail Architecture

## System Overview
Patchrail is a local-first control plane that records supervised coding-agent workflows as explicit state transitions. The MVP is a headless core with a thin CLI wrapper. It accepts a task, stores a plan, resolves role assignments through a provider and access-mode policy, records a run, persists an artifact bundle, captures a review result, and requires an explicit human approval or rejection before completion.

## Core Modules
- `patchrail.cli`: `argparse`-based command surface for task, config, preflight, plan, run, status, review, approval, fallback approval, list, logs, and artifacts commands.
- `patchrail.core`: orchestration services, role assignment resolution, preflight logic, ID generation, state transition validation, domain errors, and future hook contracts.
- `patchrail.models`: dataclasses and enums for `Task`, `Plan`, `Run`, `RunnerAssignment`, `ReviewResult`, `ApprovalRecord`, `FallbackApprovalRequest`, `PreflightSnapshot`, `ArtifactBundle`, `DecisionTrace`, and `CostMetrics`.
- `patchrail.storage`: filesystem persistence for JSON records, role-policy config, JSONL ledgers, and artifact lookup.
- `patchrail.runners`: runner interface and shell-backed local harness execution, ready to host `codex`, `claude`, and `grok` adapters.
- `patchrail.review`: review persistence and review-to-approval boundary handling.
- `patchrail.approval`: explicit task approval and fallback approval request handling plus ledger appends.
- `patchrail.artifacts`: artifact bundle creation and lookup.

## Role Ontology
Patchrail treats role selection as an auditable domain object, not an implicit runtime choice.

Core ontology terms:
- `Role`: `supervisor`, `planner`, `reviewer`, `executor`
- `Provider`: `codex`, `claude`, `grok`
- `AccessMode`: `api`, `subscription`
- `RoleCandidate`: a concrete `provider × access_mode` option for a role
- `CapabilityProfile`: declared capabilities such as planning, review, execution, JSON output, and non-interactive operation
- `RolePolicy`: ordered candidates for one role
- `RolePolicySet`: the locally persisted policy document
- `PreflightResult`: readiness checks for a candidate
- `ResolvedAssignment`: the concrete candidate selected at phase start
- `FallbackEvent`: an auditable record of primary-candidate failure and fallback selection

Hard rules:
- `Codex` remains the fixed supervisor.
- `planner`, `reviewer`, and `executor` are policy-resolved at phase start.
- Fallback is allowed, but changing `provider` or `access_mode` requires additional approval before the phase can continue.
- Persisted records remain language-neutral even if future CLI notices become bilingual.

## State Model
- `Task` is the supervisory anchor for a unit of work.
- `Plan` belongs to a task, must exist before a run can start, and stores the resolved planner assignment plus preflight evidence.
- `Run` records runner assignment, elapsed time, synthetic output, artifact bundle identity, and the resolved executor assignment plus preflight evidence.
- `ReviewResult` records the reviewer verdict, rationale, and the resolved reviewer assignment plus preflight evidence.
- `ApprovalRecord` records the human decision and rationale after review.
- `FallbackApprovalRequest` records a human-reviewed exception request when role resolution needs a blocked fallback.
- `PreflightSnapshot` records a standalone phase-resolution snapshot so operator audits can inspect preflight attempts independently from plan/run/review records.
- `DecisionTrace` is append-only and captures meaningful transitions with timestamps and summaries.
- `CostMetrics` captures stub elapsed and cost fields even before real provider integrations exist.

Task summary states for the MVP:
- `created`
- `planned`
- `running`
- `review_pending`
- `awaiting_approval`
- `approved`
- `rejected`

## Policy And Preflight Model
Role policy is stored locally under `.patchrail/config/role-policy.json`.

Phase flow:
1. Load the policy set for the requested role.
2. Filter candidates when the CLI explicitly constrains executor provider, such as `claude_code` or `grok_runner`.
3. Run preflight for each candidate.
4. Select the first ready candidate.
5. If the selected candidate differs from the primary candidate:
   - same `provider` and same `access_mode`: auto-permitted fallback
   - different `provider` or different `access_mode`: blocked until additional approval exists
6. Persist the `ResolvedAssignment`, `PreflightResult` list, and optional `FallbackEvent` into the plan, review, or run record.
7. If blocked, create a `FallbackApprovalRequest` and require `approve-fallback` or `reject-fallback` before retry.
8. Persist a standalone `PreflightSnapshot` for each `plan`, `run`, and `review` resolution attempt before the phase continues or fails.

Preflight checks:
- `api`: `credential_present`, `endpoint_configured`
- `subscription`: `cli_present`, `login_ok`, `entitlement_ok`, `noninteractive_ok`

The default local policy intentionally uses simulation-backed subscription candidates so the ontology and approval rules can be tested without live provider credentials.

## Runner Model
The runner contract is intentionally narrow:
- Accept a task and its plan.
- Execute synchronously in the MVP.
- Prepare a per-run workspace with serialized task and plan inputs.
- Return execution output, stderr, cost metrics, exit code, and artifact content.
- Avoid provider-specific control flow inside the core orchestration service.

Current adapter behavior:
- `claude_code`, `grok_runner`, `codex_runner`, and `auto` are CLI entrypoints into the executor phase.
- The selected executor candidate supplies the concrete command when a shell-backed path is used.
- Shell mode receives `PATCHRAIL_TASK_FILE`, `PATCHRAIL_PLAN_FILE`, `PATCHRAIL_OUTPUT_FILE`, `PATCHRAIL_RUN_ID`, and `PATCHRAIL_RUNNER_NAME`.
- `patchrail.runners.local_harness` is the built-in shell target for local end-to-end testing.

Real provider integrations are deferred until the state machine, storage layout, and approval boundary are stable.

## Storage Layout
Default root: `.patchrail/`

Configurable root:
- `PATCHRAIL_HOME`

Filesystem layout:
- `.patchrail/config/role-policy.json`
- `.patchrail/tasks/<task_id>.json`
- `.patchrail/plans/<plan_id>.json`
- `.patchrail/runs/<run_id>.json`
- `.patchrail/reviews/<review_id>.json`
- `.patchrail/approvals/<approval_id>.json`
- `.patchrail/fallback_requests/<request_id>.json`
- `.patchrail/preflight_snapshots/<snapshot_id>.json`
- `.patchrail/artifacts/<run_id>/bundle.json`
- `.patchrail/artifacts/<run_id>/stdout.log`
- `.patchrail/artifacts/<run_id>/stderr.log`
- `.patchrail/artifacts/<run_id>/execution-summary.md`
- `.patchrail/artifacts/<run_id>/diff-summary.md`
- `.patchrail/artifacts/<run_id>/invocation.json`
- `.patchrail/workspaces/<run_id>/task.json`
- `.patchrail/workspaces/<run_id>/plan.json`
- `.patchrail/workspaces/<run_id>/output.json`
- `.patchrail/ledgers/decision-trace.jsonl`
- `.patchrail/ledgers/approval-ledger.jsonl`
- `.patchrail/ledgers/fallback-approval-ledger.jsonl`

Read-side navigation:
- `patchrail list tasks`
- `patchrail list plans [--task-id <task_id>]`
- `patchrail list runs [--task-id <task_id>]`
- `patchrail list reviews [--task-id <task_id>]`
- `patchrail list approvals [--task-id <task_id>]`
- `patchrail list fallback-requests [--task-id <task_id>]`
- `patchrail list preflight-snapshots [--task-id <task_id>]`

## Artifact And Approval Flow
1. `config init` creates the local role-policy document used for ontology-aware local testing.
2. `task create` stores a new task and appends a decision trace.
3. `plan` resolves the planner candidate, stores the plan with preflight evidence, updates the task to `planned`, and appends decision traces.
4. Every `plan`, `run`, and `review` resolution attempt first writes a standalone `PreflightSnapshot`.
5. If role resolution hits a blocked fallback, Patchrail stores a `FallbackApprovalRequest`, appends trace and fallback-approval ledger entries, and stops the phase without mutating the task lifecycle.
6. `approve-fallback` or `reject-fallback` records the human decision for that deviation request.
7. `run` resolves the executor candidate, creates an isolated workspace, stores runner assignment metadata inside the run record, writes invocation plus stdout/stderr artifact files, updates the task to `review_pending`, and appends decision traces.
8. `review` resolves the reviewer candidate, stores the review result with rationale and preflight evidence, updates the task to `awaiting_approval`, and appends a decision trace with rationale.
9. `approve` or `reject` stores an approval record, appends both decision and approval ledger entries, and moves the task to its final state.

## Deferred Hook Contract
Future infra-ops support is represented as a hook seam, not an automation system:
- Hook input: event name plus structured payload.
- Hook registry: no-op in the MVP.
- Hook execution: deferred.

This preserves a stable integration point without expanding Patchrail into a cloud operations product before the core state machine is proven.
