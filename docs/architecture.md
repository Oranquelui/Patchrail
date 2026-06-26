# Patchrail Architecture

## System Overview
Patchrail is a local-first control plane that records supervised coding-agent workflows as explicit state transitions. The current MVP is a headless core with a thin CLI wrapper. It accepts a task, stores a plan, resolves role assignments through a provider and access-mode policy, records a run, persists an artifact bundle, captures a review result, and requires an explicit human approval or rejection before completion.

The current MVP proves the canonical workflow record, planning-brief companion artifacts, Runner Contract v1, Evidence Bundle v1, and approval boundary. The next planning layer extends the front of that workflow so operators can define what finished looks like, which concepts are real, which actions are low-risk enough to delegate, and what scope is in-bounds before implementation begins. That layer remains subordinate to the existing canonical state machine rather than replacing it.

Patchrail’s approval boundary should not become a prompt for every tool call. Repeated approvals create approval fatigue and quickly become rubber stamps. The next approval-policy layer should treat human approval as a higher-order decision: define the policy before work begins, let low-risk actions proceed inside that policy, escalate boundary crossings, and preserve enough evidence for final acceptance or rejection.

Patchrail uses the word "layer" narrowly:

| Layer | Brief / Record | Timing | Purpose |
| --- | --- | --- | --- |
| Prediction | `Future Completion Brief` | before implementation | Predict what should be true in the future, including invariants, failure conditions, and non-goals. |
| Reality boundary | `Ontology Brief` | before implementation | Define what exists, who owns it, and where approval/artifact boundaries sit. |
| Post-implementation acceptance | `Product Brief` | defined before implementation, checked after implementation | State what must be true for users and operators after the implementation exists. |
| Delegation policy | planned `ApprovalProfile` / `PermissionPolicy` | before and during run | Define which action classes are auto, ask, or deny so humans do not review every low-risk step. |
| Execution translation | canonical `Plan` | before run | Convert the three briefs into executable steps and snapshot the brief references immutably. |
| Post-implementation evidence | Harness / planned `RunLedger` / `ArtifactBundle` | during and after executor run, before review | Capture execution summary, diff summary, stdout/stderr, invocation, runner trace, action receipts, escalations, rollback notes, and artifact metadata for reviewer and human approval. |

So the short answer is: Future is prediction; Product is the after-implementation acceptance layer; Harness is the after-implementation evidence capture layer.

## Core Modules
- `patchrail.cli`: `argparse`-based command surface plus a thin render layer for setup, task, planning brief, config, start, doctor, preflight, plan, run, status, review, approval, fallback approval, list, logs, and artifacts commands. Human-readable output is the operator default; `--json` preserves machine-readable automation output.
- `patchrail.cli.shell`: a small interactive shell wrapper for `patchrail start` in TTY sessions. It reuses the canonical CLI parser and service layer instead of adding a second state machine.
- `patchrail.core`: orchestration services, role assignment resolution, preflight logic, ID generation, state transition validation, domain errors, and future hook contracts.
- `skills/patchrail-supervise`: first public Agent Skill scaffold that teaches Codex, Claude Code, Grok Build, and compatible clients how to use Patchrail’s supervision workflow without making the skill itself the canonical state owner.
- `patchrail.workflows`: pluggable auto plan/review backend contract plus the default local backend and an optional LangGraph-backed planner/reviewer scaffold.
- `patchrail.models`: dataclasses and enums for `Task`, `Plan`, plan-scoped planning brief references, `Run`, `RunnerAssignment`, `ReviewResult`, `ApprovalRecord`, `FallbackApprovalRequest`, `PreflightSnapshot`, `ArtifactBundle`, `DecisionTrace`, and `CostMetrics`. `ApprovalProfile` and `RunLedger` are planned next-model additions.
- `patchrail.storage`: filesystem persistence for JSON records, role-policy config, JSONL ledgers, planning brief companion artifacts, and artifact lookup.
- `patchrail.runners`: runner interface, shell-backed local harness execution, API-backed executor runners, and Claude-backed subscription executor runners.
- `patchrail.providers`: minimal HTTP adapters for provider-backed executor calls and workflow backends that need direct provider completion calls.
- `patchrail.review`: review persistence and review-to-approval boundary handling.
- `patchrail.approval`: explicit task approval and fallback approval request handling plus ledger appends.
- `patchrail.artifacts`: artifact bundle creation and lookup.

## Phase 1 Planning Direction
The first planning layer adds future-anchored, risk-aware planning without creating new top-level canonical records.

Planned operator flow:
1. `machine/runtime onboarding`
2. `project/planning onboarding`
3. approval profile selection
4. canonical `Plan`
5. canonical `Run`
6. canonical `ReviewResult`
7. canonical `ApprovalRecord`

Planning artifacts:
- `Future Completion Brief` / Prediction layer: what should be true in the future, including completed state, invariant constraints, failure conditions, and non-goals
- `Ontology Brief` / Reality-boundary layer: what exists, who owns it, entity relations, approval boundaries, artifact boundaries, and explicit non-entities
- `Product Brief` / Post-implementation acceptance layer: the user problem, MVP scope, acceptance criteria, operator evidence to review after implementation, and out-of-scope commitments
- `Approval Profile` / Delegation-policy layer: the low-risk actions the agent can perform without repeated prompts, the boundary crossings that require escalation, and the actions denied outright
- `Triangulated Plan Summary`: a comparison layer across distinct planning participants before Patchrail stores the canonical plan

Phase 1 constraints:
- The three briefs are stored as plan-scoped companion artifacts, not new canonical lifecycle records.
- Operators can create, list, and show them through `patchrail brief create|list|show`.
- Operators can run `patchrail brief validate` to inspect v1 sequence readiness without mutating lifecycle state or blocking manual plan creation.
- Brief content is persisted locally under `.patchrail/briefs/` with a SHA-256 digest. When a plan is created, the plan stores stable `planning_briefs` references to the task's current briefs.
- Brief records and plan-scoped brief references declare `schema_version=patchrail.brief_schema.v1` so future sessions can reconstruct the companion-artifact contract used for planning.
- The canonical lifecycle remains `Task -> Plan -> Run -> ReviewResult -> ApprovalRecord`.
- Approval meaning, ledgers, and artifact ownership remain Patchrail-owned.
- Low-risk action approval is policy-owned, not prompt-owned. The operator should not need to approve every scoped edit, local test, lint, typecheck, or artifact write.
- LangGraph may help produce planning candidates, but it does not own the planning ontology, approval semantics, or canonical state transitions.

Planned provider roles for supervised planning:
- `Codex / OpenAI`: supervisory structuring lens for the canonical plan
- `Claude`: implementation expansion lens for coherent build paths
- `Grok`: challenge lens for contradiction finding, missing constraints, and drift detection

## Skill-First Distribution Model
Patchrail should be usable as a direct CLI, but the preferred operator experience is skill-first and CLI-backed.

Distribution surfaces:
- `patchrail` CLI: local persistence, policy inspection, state transitions, artifact lookup, smoke tests, and deterministic automation.
- `skills/patchrail-supervise`: reusable instructions that guide Codex, Claude Code, Grok Build, and compatible agents through scoped delegation, evidence capture, escalation, and final review.
- Codex plugin package: installable distribution for Codex that can bundle the skill, optional hooks, assets, and future MCP configuration.
- Claude Code / Grok Build compatibility: the skill should stay close to the open `SKILL.md` format so it can run in those agents without requiring a Patchrail-specific chat UI.

Hard boundaries:
- A skill is not the enforcement layer. It can instruct an agent to use Patchrail correctly, but enforcement must come from the host agent’s sandbox/permission system, Patchrail policy records, hooks where available, and local evidence.
- Patchrail should record the effective native approval mode where possible, such as Codex approval/sandbox settings, Claude permission mode, or Grok plugin/hook configuration.
- The CLI remains the source of truth for `.patchrail/` state. Agent skills may call it, but they do not own canonical lifecycle state.

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
- A `Plan` may also reference a `Future Completion Brief`, `Ontology Brief`, `Product Brief`, and future triangulated planning metadata as companion artifacts. Those supporting documents do not replace the canonical plan record.
- `Run` records runner assignment, elapsed time, synthetic output, artifact bundle identity, and the resolved executor assignment plus preflight evidence.
- Planned `ApprovalProfile` records auto, ask, and deny action classes for a task or run. It is the primary defense against approval fatigue because routine low-risk actions are delegated by policy rather than by repeated prompts.
- Planned `RunLedger` records the effective profile, auto-approved action classes, escalations, denials, receipts, and rollback notes observed during execution.
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
Approval profiles are planned under `.patchrail/config/approval-profiles.json` or task-scoped companion records. The next implementation should start with a conservative local default before adding custom profile editing.

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

Approval profile defaults:
- `auto`: repo-local reads, scoped file edits in the active workspace, local tests, lint, typecheck, formatters, read-only git inspection, and writes to approved artifact directories
- `ask`: dependency installation, lockfile edits, CI/auth/deployment/database changes, broad network access, external comments, branch pushes, PR creation, preview deploys, and production API calls
- `deny`: secrets access, credential exfiltration, destructive filesystem operations outside the workspace, writes to protected branches, final approval by an agent, and merge/deploy actions unless an explicit future policy grants them

Preflight checks:
- `api`: `credential_present`, `endpoint_configured`
- `subscription`: `cli_present`, `login_ok`, `entitlement_ok`, `noninteractive_ok`

`real` preset subscription behavior:
- `codex subscription`: `codex login status`
- `claude subscription`: `claude auth status`

`grok` is API-only in the default policy set. Patchrail does not currently ship a default `grok subscription` candidate because the CLI contract is not yet stable enough for supervised runtime use.

The default `local` policy intentionally uses simulation-backed candidates so the ontology and approval rules can be tested without live provider credentials. The `real` preset switches readiness truthfulness on and enables only the live paths that Patchrail can currently supervise safely.

## Onboarding Model
Patchrail is moving toward a two-pass onboarding model.

`machine/runtime onboarding` configures what this machine can supervise:
- preset selection such as `local` or `real`
- provider set selection across `codex`, `claude`, and `grok`
- access-mode selection across `api` and `subscription`
- workflow backend selection across `local` and optional `langgraph`
- planned approval profile selection across conservative, balanced, and sandboxed-autonomy presets
- readiness verification through `doctor` and role preflight
- first-run setup through `patchrail setup`, which bootstraps config, runs the same preflight summary as `doctor`, and prints concrete next commands

`project/planning onboarding` configures what this project is trying to finish:
- create the task anchor
- define the `Future Completion Brief`
- define the `Ontology Brief`
- define the `Product Brief`
- select or create the task’s approval profile once `ApprovalProfile v1` exists
- generate a canonical plan from those constraints
- first-run project setup through `patchrail setup project`, which can create the task anchor and write editable local brief scaffolds before explicit `brief create` and `plan`

Phase 1 treats the three-provider setup as recommended rather than universally required. If one or more providers are unavailable, Patchrail should remain usable while surfacing that triangulated planning is degraded.

## Runner Model
The runner contract is intentionally narrow:
- Accept a task and its plan.
- Execute synchronously in the MVP.
- Prepare a per-run workspace with serialized task and plan inputs.
- Return execution output, stderr, cost metrics, exit code, and artifact content.
- Avoid provider-specific control flow inside the core orchestration service.
- Declare the v1 workspace and environment handoff in `docs/contracts/runner-contract-v1.md`.

Current adapter behavior:
- `claude_code`, `grok_runner`, `codex_runner`, and `auto` are CLI entrypoints into the executor phase.
- The selected executor candidate supplies the concrete command when a shell-backed path is used.
- When the selected executor candidate uses `access_mode=api`, Patchrail routes the run through a provider HTTP adapter instead of the local harness.
- When the selected executor candidate uses `access_mode=subscription`, Patchrail routes the run through a provider-specific subscription adapter instead of the local harness.
- Shell mode receives reserved Runner Contract v1 variables for the contract schema version, run id, runner name, workspace path, task file, plan file, output file, runner artifact directory, and runner trace file.
- Operators can inspect the read-only contract surface with `patchrail contracts runner` or `patchrail --json contracts runner`.
- `patchrail.runners.local_harness` is the built-in shell target for local end-to-end testing. Its trace records observed reserved environment variables, workspace-relative handoff paths, and runner-writable path readiness so operators can verify the v1 contract was injected at runtime.
- Runner-local files written under `.patchrail/workspaces/<run_id>/artifacts/` are copied into the canonical evidence bundle under `.patchrail/artifacts/<run_id>/runner-artifacts/` and recorded as `runner_artifact` manifest entries.
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
- `.patchrail/config/approval-profiles.json` planned
- `.patchrail/tasks/<task_id>.json`
- `.patchrail/briefs/<brief_id>.json`
- `.patchrail/plans/<plan_id>.json`
- `.patchrail/runs/<run_id>.json`
- `.patchrail/run_ledgers/<run_id>.json` planned
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
- `.patchrail/artifacts/<run_id>/runner-artifacts/` when the runner writes local artifact files
- `.patchrail/workspaces/<run_id>/task.json`
- `.patchrail/workspaces/<run_id>/plan.json`
- `.patchrail/workspaces/<run_id>/output.json`
- `.patchrail/workspaces/<run_id>/artifacts/` reserved for runner-local artifact exchange
- `.patchrail/workspaces/<run_id>/trace.json` reserved for runner-local trace exchange
- `.patchrail/ledgers/decision-trace.jsonl`
- `.patchrail/ledgers/approval-ledger.jsonl`
- `.patchrail/ledgers/fallback-approval-ledger.jsonl`

Read-side navigation:
- `patchrail list tasks`
- `patchrail contracts runner`
- `patchrail brief list --task-id <task_id>`
- `patchrail brief show --brief-id <brief_id>`
- `patchrail list plans [--task-id <task_id>]`
- `patchrail list runs [--task-id <task_id>]`
- `patchrail list reviews [--task-id <task_id>]`
- `patchrail list approvals [--task-id <task_id>]`
- `patchrail list fallback-requests [--task-id <task_id>]`
- `patchrail list preflight-snapshots [--task-id <task_id>]`
- `patchrail list artifact-bundles [--task-id <task_id>] [--logical-kind <kind>] [--has-trace]`
- `patchrail status --task-id <task_id>` also surfaces `latest_artifact_bundle` for the current run when one exists

## Artifact And Approval Flow
1. `setup` or `config init [--preset local|real]` creates the local role-policy document used for ontology-aware testing.
2. `task create` stores a new task and appends a decision trace.
3. `setup project` can create a task and write editable local brief scaffolds. After the operator replaces placeholder content, `brief create` stores a `future`, `ontology`, or `product` companion artifact for that task, records its digest, and appends a decision trace without changing task lifecycle state.
4. `plan` resolves the planner candidate, optionally auto-generates plan content through the selected workflow backend, stores the plan with preflight evidence, planning brief references, plus any auxiliary workflow metadata, updates the task to `planned`, and appends decision traces.
5. Every `plan`, `run`, and `review` resolution attempt first writes a standalone `PreflightSnapshot`.
6. If role resolution hits a blocked fallback, Patchrail stores a `FallbackApprovalRequest`, appends trace and fallback-approval ledger entries, and stops the phase without mutating the task lifecycle.
7. `approve-fallback` or `reject-fallback` records the human decision for that deviation request.
8. `run` resolves the executor candidate, creates an isolated workspace, stores runner assignment metadata inside the run record, writes invocation plus stdout/stderr artifact files, updates the task to `review_pending`, and appends decision traces.
   - Artifact bundles declare `schema_version=patchrail.evidence_bundle.v1` so status, artifact lookup, and history queries expose the post-run evidence contract used for review.
   - Artifact bundles now include manifest-style metadata per file, including logical kind, media type, collection status, digest, and byte size.
   - Runner adapters may also return an optional structured trace, which Patchrail persists as another artifact without giving the runner ownership of the canonical run record.
   - Runner adapters may write files to the reserved workspace artifact directory; Patchrail copies those files into canonical artifact storage before manifest persistence.
   - Read-side lookup stays Patchrail-owned: the latest bundle is exposed through `status`, and historical bundle queries stay under the CLI list surface.
9. `review` resolves the reviewer candidate, optionally auto-generates review content through the selected workflow backend, stores the review result with rationale and preflight evidence plus any auxiliary workflow metadata, updates the task to `awaiting_approval`, and appends a decision trace with rationale.
10. `approve` or `reject` stores the final human outcome decision, appends both decision and approval ledger entries, and moves the task to its final state. This approval accepts or rejects the outcome and evidence; it is not a claim that the human manually approved every intermediate action.

## Deferred Hook Contract
Future infra-ops support is represented as a hook seam, not an automation system:
- Hook input: event name plus structured payload.
- Hook registry: no-op in the MVP.
- Hook execution: deferred.

This preserves a stable integration point without expanding Patchrail into a cloud operations product before the core state machine is proven.
