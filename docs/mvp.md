# Patchrail MVP

## Goal
Prove Patchrail’s thesis with the narrowest possible supervised workflow: a task can be created, planned, resolved through role-aware policy and preflight, executed locally, reviewed, explicitly approved or rejected, and safely resumed from local disk alone.

## In Scope
- CLI commands for config bootstrap, preflight inspection, task creation, planning, execution, status, review, approval, rejection, logs, and artifact lookup.
- Filesystem persistence under `.patchrail/` or `PATCHRAIL_HOME`.
- CLI-visible workflow backend selection persisted under local config, with `local` as default and `langgraph` as an optional backend.
- Role ontology for `planner`, `reviewer`, and `executor` across `codex`, `claude`, and `grok` with `api` and `subscription` access modes.
- Supervised `plan --auto` and `review --auto` paths behind a pluggable workflow backend seam, with canonical records still owned by Patchrail.
- Deterministic local harness execution through shell-backed commands, with policy-resolved candidates supplying the concrete command.
- Artifact bundle persistence from day one.
- Per-run isolated workspaces containing task, plan, and runner output manifests.
- A repo-local smoke path via `scripts/local_smoke_test.sh` and `patchrail.runners.local_harness`.
- Local policy config plus persisted `ResolvedAssignment`, `PreflightResult`, and `FallbackEvent` data in plan, review, and run records.
- Decision trace and approval ledger persistence.
- Minimal tests covering happy path, invalid transitions, role-policy resolution, and resumption from disk.

## Acceptance Criteria
- `patchrail config init` creates a local role-policy document and persists the selected workflow backend.
- `patchrail preflight` reports role candidate readiness from local state and environment only.
- `patchrail task create` creates a task and persists it locally.
- `patchrail plan` resolves and persists a planner assignment, stores a plan, and moves the task to `planned`.
- `patchrail plan --auto` routes through the configured workflow backend without changing Patchrail's canonical plan record ownership.
- `patchrail run` requires an existing plan, resolves and persists an executor assignment, stores a run, writes artifact files plus invocation metadata, creates an isolated workspace, and moves the task to `review_pending`.
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
