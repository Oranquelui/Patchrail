# Patchrail MVP

## Goal
Prove Patchrail’s thesis with the narrowest possible supervised workflow: a task can be created, planned, resolved through role-aware policy and preflight, executed locally, verified with operator-specified checks, reviewed, explicitly approved or rejected, exported as an approval packet, and safely resumed from local disk alone.

## In Scope
- CLI commands for setup bootstrap, config bootstrap, preflight inspection, task creation, Delivery Contract scaffolding through existing planning brief storage, planning, execution, verification, packet export, review-queue listing, status, review, approval, rejection, logs, and artifact lookup.
- A CLI onboarding shell via `patchrail start`, with `patchrail start --once` as the non-interactive splash path.
- Filesystem persistence under `.patchrail/` or `PATCHRAIL_HOME`.
- CLI-visible workflow backend selection persisted under local config, with `local` as default and `langgraph` as an optional backend.
- Role ontology for `planner`, `reviewer`, and `executor` across `codex`, `claude`, and `grok` with `api` and `subscription` access modes.
- Supervised `plan --auto` and `review --auto` paths behind a pluggable workflow backend seam, with canonical records still owned by Patchrail.
- Deterministic local harness execution through shell-backed commands, with policy-resolved candidates supplying the concrete command.
- Artifact bundle persistence from day one.
- Verification record persistence from day one for command, cwd, exit code, stdout/stderr output paths, elapsed time, task id, and run id.
- Approval packet generation as a read model rather than a new lifecycle entity.
- Per-run isolated workspaces containing task, plan, and runner output manifests.
- A repo-local smoke path via `scripts/local_smoke_test.sh` and `patchrail.runners.local_harness`.
- Local policy config plus persisted `ResolvedAssignment`, `PreflightResult`, and `FallbackEvent` data in plan, review, and run records.
- Decision trace and approval ledger persistence.
- Minimal tests covering happy path, invalid transitions, role-policy resolution, and resumption from disk.

## Acceptance Criteria
- `patchrail config init` creates a local role-policy document and persists the selected workflow backend.
- `patchrail setup` bootstraps runtime config, reports preflight status, and returns concrete next commands.
- `patchrail setup project --guided` creates or reuses a task and writes editable local Delivery Contract prompts for Future Completion, Ontology, and Product brief scaffolds; operators persist edited brief content with `patchrail brief create` before plan creation.
- `patchrail start` can bootstrap config and keep an operator in a TTY shell without introducing a second canonical state model.
- `patchrail preflight` reports role candidate readiness from local state and environment only.
- `patchrail task create` creates a task and persists it locally.
- `patchrail plan` resolves and persists a planner assignment, stores a plan, and moves the task to `planned`.
- `patchrail plan --auto` routes through the configured workflow backend without changing Patchrail's canonical plan record ownership.
- `patchrail run` requires an existing plan, resolves and persists an executor assignment, stores a run, writes artifact files plus invocation metadata, creates an isolated workspace, and moves the task to `review_pending`.
- `patchrail verify --run-id <run_id> --command "<shell command>"` runs an operator-specified verification command, stores stdout/stderr artifacts, records exit code and elapsed time, and does not mutate the canonical task lifecycle.
- `patchrail list verifications` filters verification records by task or run.
- `patchrail list review-queue` groups tasks by missing verification, failed verification, review readiness, approval readiness, and approved state.
- `patchrail packet show|export` renders Markdown or JSON approval packets from existing local records and surfaces unresolved gaps.
- `patchrail review` requires a completed run, resolves and persists a reviewer assignment, stores the verdict and rationale, and moves the task to `awaiting_approval`.
- `patchrail review --auto` routes through the configured workflow backend without changing approval, ledger, or artifact ownership.
- `patchrail approve` and `patchrail reject` require a completed review and store human rationale plus ledger entries.
- Cross-provider or cross-access-mode fallback is blocked until additional approval exists.
- `patchrail status`, `patchrail logs`, and `patchrail artifacts` reconstruct output entirely from persisted local state.
- Future sessions can resume by reading the stored files without in-memory context.

## Out Of Scope
- Real provider SDK integrations.
- Background workers or distributed execution.
- Worktree management beyond future runner needs.
- Web dashboards or GUI review surfaces.
- Autonomous verification command selection.
- Fully autonomous planning/execution, autonomous approvals, or merge automation.
- LangGraph-driven executor orchestration or backend-owned approval state.
- LangGraph Studio or any dashboard-first operator workflow.
- Full localization of every CLI message beyond the current structured-output discipline.
- Infrastructure automation beyond a placeholder hook contract.

## MVP Discipline
- Choose inspectability over abstraction.
- Prefer one clear path through the workflow over broad autonomous branching.
- Keep saved data language-neutral even if CLI notices become bilingual later.
- Avoid schema churn until the local state flow feels stable under repeated use.
