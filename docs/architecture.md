# Patchrail Architecture

## System Overview
Patchrail is a local-first control plane that records supervised coding-agent workflows as explicit state transitions. The MVP is a headless core with a thin CLI wrapper. It accepts a task, stores a plan, resolves role assignments through a provider and access-mode policy, records a run, persists an artifact bundle, captures a review result, and requires an explicit human approval or rejection before completion.

## Core Modules
- `patchrail.cli`: `argparse`-based command surface plus a thin render layer for task, config, doctor, preflight, plan, run, status, review, approval, fallback approval, list, logs, and artifacts commands. Human-readable output is the operator default; `--json` preserves machine-readable automation output.
- `patchrail.core`: orchestration services, role assignment resolution, preflight logic, ID generation, state transition validation, domain errors, and future hook contracts.
- `patchrail.workflows`: pluggable auto plan/review backend contract plus the default local backend and an optional LangGraph-backed planner/reviewer scaffold.
- `patchrail.models`: dataclasses and enums for `Task`, `Plan`, `Run`, `RunnerAssignment`, `ReviewResult`, `ApprovalRecord`, `FallbackApprovalRequest`, `PreflightSnapshot`, `ArtifactBundle`, `DecisionTrace`, and `CostMetrics`.
- `patchrail.storage`: filesystem persistence for JSON records, role-policy config, JSONL ledgers, and artifact lookup.
- `patchrail.runners`: runner interface, shell-backed local harness execution, API-backed executor runners, and Claude-backed subscription executor runners.
- `patchrail.providers`: minimal HTTP adapters for provider-backed executor calls and workflow backends that need direct provider completion calls.
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

Candidate details may also include:
- `model`: the provider model to use for API-backed execution
- `cli_command`: the executable used for subscription health checks

Hard rules:
- `Codex` remains the fixed supervisor.
- `planner`, `reviewer`, and `executor` are policy-resolved at phase start.
- Fallback is allowed, but changing `provider` or `access_mode` requires additional approval before the phase can continue.
- Persisted records remain language-neutral even if future CLI notices become bilingual.

## State Model
- `Task` is the supervisory anchor for a unit of work.
- `Plan` belongs to a task, must exist before a run can start, and stores the resolved planner assignment plus preflight evidence. Auto-generated plans may also store auxiliary workflow backend metadata, but the canonical plan record remains Patchrail-owned.
- `Run` records runner assignment, elapsed time, synthetic output, artifact bundle identity, and the resolved executor assignment plus preflight evidence.
- `ReviewResult` records the reviewer verdict, rationale, and the resolved reviewer assignment plus preflight evidence. Auto-generated reviews may also store auxiliary workflow backend metadata, but approval meaning remains outside the backend.
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
Workflow backend selection is stored locally under `.patchrail/config/workflow-backend.json`, with `PATCHRAIL_WORKFLOW_BACKEND` reserved as an explicit temporary override.

Config presets:
- `local`: simulation-backed role policy for deterministic local testing
- `real`: live-readiness role policy for Codex, Claude, and Grok API/subscription checks with selective live plan/run adapters where Patchrail can supervise them safely

Phase flow:
1. Load the policy set for the requested role.
2. Filter candidates when the CLI explicitly constrains executor provider, such as `claude_code` or `grok_runner`.
3. Filter candidates further when the CLI explicitly constrains `access_mode`, such as `--access-mode api`.
4. Run preflight for each candidate.
5. Select the first ready candidate.
6. If the selected candidate differs from the primary candidate:
   - same `provider` and same `access_mode`: auto-permitted fallback
   - different `provider` or different `access_mode`: blocked until additional approval exists
7. Persist the `ResolvedAssignment`, `PreflightResult` list, and optional `FallbackEvent` into the plan, review, or run record.
8. If blocked, create a `FallbackApprovalRequest` and require `approve-fallback` or `reject-fallback` before retry.
9. Persist a standalone `PreflightSnapshot` for each `plan`, `run`, and `review` resolution attempt before the phase continues or fails.

Preflight checks:
- `api`: `credential_present`, `endpoint_configured`
- `subscription`: `cli_present`, `login_ok`, `entitlement_ok`, `noninteractive_ok`

`real` preset subscription behavior:
- `codex subscription`: `codex login status`
- `claude subscription`: `claude auth status`

`grok` is API-only in the default policy set. Patchrail does not currently ship a default `grok subscription` candidate because the CLI contract is not yet stable enough for supervised runtime use.

The default `local` policy intentionally uses simulation-backed candidates so the ontology and approval rules can be tested without live provider credentials. The `real` preset switches readiness truthfulness on and enables only the live paths that Patchrail can currently supervise safely.

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
- When the selected executor candidate uses `access_mode=api`, Patchrail routes the run through a provider HTTP adapter instead of the local harness.
- When the selected executor candidate uses `access_mode=subscription`, Patchrail routes the run through a provider-specific subscription adapter instead of the local harness.
- Shell mode receives `PATCHRAIL_TASK_FILE`, `PATCHRAIL_PLAN_FILE`, `PATCHRAIL_OUTPUT_FILE`, `PATCHRAIL_RUN_ID`, and `PATCHRAIL_RUNNER_NAME`.
- `patchrail.runners.local_harness` is the built-in shell target for local end-to-end testing.
- API mode currently supports:
  - `codex api` via OpenAI Responses API
  - `claude api` via Anthropic Messages API
  - `grok api` via xAI Chat Completions API
- Subscription mode currently supports:
  - `codex subscription` via `codex exec --json --output-last-message ...`
  - `claude subscription` via `claude -p --output-format json`

Planner / reviewer automation:
- `plan --auto` and `review --auto` resolve their candidates in the core service, then delegate content generation through the `WorkflowEngine` contract.
- The default backend is `patchrail.workflows.local.LocalWorkflowEngine`, which preserves the current deterministic local simulation and direct provider-completion behavior.
- `patchrail.workflows.langgraph_backend.LangGraphWorkflowEngine` is optional and subordinate. It may hold backend workflow state, but it does not own the canonical task lifecycle, approval boundary, artifact bundle, approval ledger, or decision trace.
- Workflow backend selection is CLI-first through `config init --workflow-backend ...`, persisted under `.patchrail/config/workflow-backend.json`, and can be overridden temporarily via `PATCHRAIL_WORKFLOW_BACKEND`.
- The current LangGraph MVP backend compiles stateless planner/reviewer graphs with explicit `collect -> generate -> validate -> finalize` nodes and returns the executed `node_trace` as auxiliary metadata on the canonical plan/review records.
- Missing optional LangGraph dependencies fail only when an auto plan/review path tries to initialize that backend.
- Local preset uses deterministic simulated generation for both planner and reviewer workflows.
- Live workflow generation currently supports:
  - planner: `claude subscription`, `codex api`
  - reviewer: `codex subscription`, `claude api`
- `codex subscription` is currently a reviewer / executor live path. Planner auto workflows do not delegate to Codex subscription yet.
- Unsupported live candidates fail loudly instead of silently downgrading to manual or stub behavior.

## Storage Layout
Default root: `.patchrail/`

Configurable root:
- `PATCHRAIL_HOME`

Filesystem layout:
- `.patchrail/config/role-policy.json`
- `.patchrail/config/workflow-backend.json`
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
- `.patchrail/artifacts/<run_id>/trace.json` when the runner returns structured trace data
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
- `patchrail list artifact-bundles [--task-id <task_id>] [--logical-kind <kind>] [--has-trace]`
- `patchrail status --task-id <task_id>` also surfaces `latest_artifact_bundle` for the current run when one exists

## Artifact And Approval Flow
1. `config init [--preset local|real]` creates the local role-policy document used for ontology-aware testing.
2. `task create` stores a new task and appends a decision trace.
3. `plan` resolves the planner candidate, optionally auto-generates plan content through the selected workflow backend, stores the plan with preflight evidence plus any auxiliary workflow metadata, updates the task to `planned`, and appends decision traces.
4. Every `plan`, `run`, and `review` resolution attempt first writes a standalone `PreflightSnapshot`.
5. If role resolution hits a blocked fallback, Patchrail stores a `FallbackApprovalRequest`, appends trace and fallback-approval ledger entries, and stops the phase without mutating the task lifecycle.
6. `approve-fallback` or `reject-fallback` records the human decision for that deviation request.
7. `run` resolves the executor candidate, creates an isolated workspace, stores runner assignment metadata inside the run record, writes invocation plus stdout/stderr artifact files, updates the task to `review_pending`, and appends decision traces.
   - Artifact bundles now include manifest-style metadata per file, including logical kind, media type, collection status, digest, and byte size.
   - Runner adapters may also return an optional structured trace, which Patchrail persists as another artifact without giving the runner ownership of the canonical run record.
   - Read-side lookup stays Patchrail-owned: the latest bundle is exposed through `status`, and historical bundle queries stay under the CLI list surface.
8. `review` resolves the reviewer candidate, optionally auto-generates review content through the selected workflow backend, stores the review result with rationale and preflight evidence plus any auxiliary workflow metadata, updates the task to `awaiting_approval`, and appends a decision trace with rationale.
9. `approve` or `reject` stores an approval record, appends both decision and approval ledger entries, and moves the task to its final state.

## Deferred Hook Contract
Future infra-ops support is represented as a hook seam, not an automation system:
- Hook input: event name plus structured payload.
- Hook registry: no-op in the MVP.
- Hook execution: deferred.

This preserves a stable integration point without expanding Patchrail into a cloud operations product before the core state machine is proven.
