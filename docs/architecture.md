# Patchrail Architecture

## System Overview

Patchrail is a local-first control plane that records supervised AI coding-agent workflows as explicit state transitions. The MVP is a headless core with a thin CLI wrapper. It accepts a task, stores a plan, resolves role assignments through a provider and access-mode policy, records a run, persists an artifact bundle, records verification evidence, captures a review result, and requires an explicit human approval or rejection before completion.

The current alpha proves the canonical workflow record, planning-brief companion artifacts, Runner Contract v1, Evidence Bundle v1, verification records, approval packets, and the approval boundary. The next planning layer extends the front of that workflow so operators can define what finished looks like, which concepts are real, which actions are low-risk enough to delegate, and what scope is in-bounds before implementation begins.

Patchrail’s approval boundary should not become a prompt for every tool call. Repeated approvals create approval fatigue and quickly become rubber stamps. The next approval-policy layer should treat human approval as a higher-order decision: define the policy before work begins, let low-risk actions proceed inside that policy, escalate boundary crossings, and preserve enough evidence for final acceptance or rejection.

Patchrail uses the word "layer" narrowly:

| Layer | Brief / Record | Timing | Purpose |
| --- | --- | --- | --- |
| Prediction | `Future Completion Brief` | before implementation | Predict what should be true in the future, including invariants, failure conditions, and non-goals. |
| Reality boundary | `Ontology Brief` | before implementation | Define what exists, who owns it, and where approval/artifact boundaries sit. |
| Post-implementation acceptance | `Product Brief` | defined before implementation, checked after implementation | State what must be true for users and operators after the implementation exists. |
| Delegation policy | planned `ApprovalProfile` / `PermissionPolicy` | before and during run | Define which action classes are auto, ask, or deny so humans do not review every low-risk step. |
| Execution translation | canonical `Plan` | before run | Convert the briefs into executable steps and snapshot brief references immutably. |
| Post-implementation evidence | `ArtifactBundle` / `VerificationRecord` / planned `RunLedger` | after executor run, before review | Capture execution output, artifact metadata, verification commands, exit codes, command output paths, action receipts, escalations, and rollback notes for reviewer and human approval. |

## Core Modules

- `patchrail.cli`: `argparse` command surface plus human-readable rendering for setup, task, planning brief, config, start, doctor, contracts, preflight, plan, run, verify, packet, status, review, approval, fallback approval, list, logs, and artifacts commands.
- `patchrail.cli.shell`: interactive shell wrapper for `patchrail start` in TTY sessions.
- `patchrail.core`: orchestration services, role assignment resolution, preflight logic, ID generation, state transition validation, domain errors, and future hook contracts.
- `patchrail.models`: dataclasses and enums for canonical records, planning brief references, artifact bundles, verification records, decision traces, and cost metrics. `ApprovalProfile` and `RunLedger` are planned next-model additions.
- `patchrail.storage`: filesystem persistence for JSON records, config, JSONL ledgers, planning brief companion artifacts, verification outputs, and artifact lookup.
- `patchrail.runners`: runner interface, shell-backed local harness execution, API-backed executor runners, and subscription executor runners.
- `patchrail.verification`: operator-specified verification command execution and persistence.
- `patchrail.packet`: approval packet read model built from existing local records.
- `patchrail.workflows`: pluggable auto plan/review backend contract plus local and optional LangGraph-backed planner/reviewer implementations.
- `skills/patchrail-supervise`: first public Agent Skill scaffold for compatible coding-agent hosts.

## Skill-First Distribution Model

Patchrail should be usable as a direct CLI, but the preferred operator experience is skill-first and CLI-backed.

Distribution surfaces:

- `patchrail` CLI: local persistence, policy inspection, state transitions, artifact lookup, verification records, approval packets, smoke tests, and deterministic automation.
- `skills/patchrail-supervise`: reusable instructions that guide Codex, Claude Code, Grok Build, and compatible agents through scoped delegation, evidence capture, escalation, verification, and final review.
- Codex plugin package: future installable distribution that can bundle the skill, optional hooks, assets, and MCP configuration.
- Claude Code / Grok Build compatibility: the skill should stay close to the open `SKILL.md` format so it can run in those agents without requiring a Patchrail-specific chat UI.

Hard boundaries:

- A skill is not the enforcement layer. It can instruct an agent to use Patchrail correctly, but enforcement must come from the host agent’s sandbox/permission system, Patchrail policy records, hooks where available, and local evidence.
- Patchrail should record the effective native approval mode where possible, such as Codex approval/sandbox settings, Claude permission mode, or Grok plugin/hook configuration.
- The CLI remains the source of truth for `.patchrail/` state. Agent skills may call it, but they do not own canonical lifecycle state.

## State Model

- `Task` is the supervisory anchor for a unit of work.
- `Plan` belongs to a task, must exist before a run can start, and stores resolved planner assignment plus preflight evidence.
- A `Plan` may reference `Future Completion Brief`, `Ontology Brief`, and `Product Brief` companion artifacts.
- `Run` records runner assignment, elapsed time, output summary, artifact bundle identity, workspace path, and resolved executor assignment.
- `VerificationRecord` records command, cwd, exit code, status, stdout/stderr paths, elapsed time, task id, and run id.
- `ReviewResult` records reviewer verdict, rationale, and resolved reviewer assignment.
- `ApprovalRecord` records the human decision and rationale after review.
- `FallbackApprovalRequest` records a human-reviewed exception request when role resolution needs a blocked fallback.
- `PreflightSnapshot` records standalone phase-resolution attempts for audit.
- `DecisionTrace` is append-only and captures meaningful transitions.
- Planned `ApprovalProfile` records auto, ask, and deny action classes for a task or run.
- Planned `RunLedger` records effective profile, auto-approved action classes, escalations, denials, receipts, and rollback notes.

Task summary states:

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
Approval profiles are planned under `.patchrail/config/approval-profiles.json` or task-scoped companion records.

Config presets:

- `local`: simulation-backed role policy for deterministic local testing.
- `real`: live-readiness role policy for Codex, Claude, and Grok API/subscription checks with selective live adapters where Patchrail can supervise them safely.

Phase flow:

1. Load the policy set for the requested role.
2. Filter candidates when the CLI explicitly constrains provider or `access_mode`.
3. Run preflight for each candidate.
4. Select the first ready candidate.
5. If selected candidate changes provider or access mode, block until fallback approval exists.
6. Persist resolved assignment, preflight results, and optional fallback event.
7. Persist a standalone `PreflightSnapshot` for each `plan`, `run`, and `review` resolution attempt.

Planned approval profile defaults:

- `auto`: repo-local reads, scoped file edits, local tests, lint, typecheck, formatters, read-only git inspection, and writes to approved artifact directories.
- `ask`: dependency installation, lockfile edits, CI/auth/deployment/database changes, broad network access, external comments, branch pushes, PR creation, preview deploys, and production API calls.
- `deny`: secrets access, credential exfiltration, destructive filesystem operations outside the workspace, writes to protected branches, final approval by an agent, and merge/deploy actions unless explicit future policy grants them.

## Runner And Verification Model

The runner contract is intentionally narrow:

- Accept a task and plan snapshot.
- Execute synchronously in the MVP.
- Prepare a per-run workspace with serialized task and plan inputs.
- Return execution output, stderr, cost metrics, exit code, optional runner trace, and runner-local artifacts.
- Avoid provider-specific control flow inside core orchestration.
- Declare the v1 workspace and environment handoff in `docs/contracts/runner-contract-v1.md`.

Current adapter behavior:

- `claude_code`, `grok_runner`, `codex_runner`, and `auto` are CLI entrypoints into the executor phase.
- Shell mode receives reserved Runner Contract v1 variables for schema version, run id, runner name, workspace path, task file, plan file, output file, artifact directory, and trace file.
- Operators can inspect the read-only contract surface with `patchrail contracts runner`.
- Runner-local files under `.patchrail/workspaces/<run_id>/artifacts/` are copied into canonical artifact storage and recorded as `runner_artifact` manifest entries.

Verification is separate from run execution:

- `patchrail verify --run-id <run_id> --command "<command>"` runs an operator-specified shell command.
- The command does not mutate task lifecycle state.
- stdout/stderr are persisted under `.patchrail/verification_outputs/<verification_id>/`.
- `patchrail list verifications` and `patchrail list review-queue` expose verification state for review.
- `patchrail packet show|export` builds Markdown or JSON approval packets from existing records.

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
- `.patchrail/verifications/<verification_id>.json`
- `.patchrail/verification_outputs/<verification_id>/stdout.log`
- `.patchrail/verification_outputs/<verification_id>/stderr.log`
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
- `.patchrail/workspaces/<run_id>/artifacts/`
- `.patchrail/workspaces/<run_id>/trace.json`
- `.patchrail/ledgers/decision-trace.jsonl`
- `.patchrail/ledgers/approval-ledger.jsonl`
- `.patchrail/ledgers/fallback-approval-ledger.jsonl`

## Artifact, Verification, And Approval Flow

1. `setup` or `config init` creates the local role-policy document.
2. `task create` stores a task and appends a decision trace.
3. `setup project --guided` can create a task and write editable Delivery Contract brief scaffolds.
4. `brief create` stores `future`, `ontology`, or `product` companion artifacts and records digests without changing task lifecycle state.
5. `plan` resolves the planner candidate, stores the plan with preflight evidence and brief references, moves the task to `planned`, and appends decision traces.
6. `run` resolves the executor candidate, creates a workspace, stores runner assignment metadata, creates an Evidence Bundle v1 artifact bundle, moves the task to `review_pending`, and appends decision traces.
7. `verify` stores command evidence for a run without moving task state.
8. `packet show|export` reads existing local records and renders review-ready approval packets.
9. `review` resolves the reviewer candidate, stores verdict and rationale, moves the task to `awaiting_approval`, and appends decision traces.
10. `approve` or `reject` stores the final human outcome decision, appends decision and approval ledger entries, and moves the task to its final state.

## Deferred Hook Contract

Future infra-ops support is represented as a hook seam, not an automation system:

- Hook input: event name plus structured payload.
- Hook registry: no-op in the MVP.
- Hook execution: deferred.

This preserves a stable integration point without expanding Patchrail into a cloud operations product before the core state machine is proven.
