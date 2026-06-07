# Patchrail MVP

## Goal

Prove Patchrail’s revised thesis with the narrowest useful supervised workflow: an operator can define task intent, scope, completion evidence, and verification commands, then let a coding agent work while Patchrail preserves plans, runs, verification records, evidence bundles, review results, approval packets, final approval decisions, and safe continuation state on disk.

Patchrail is not trying to make humans approve every tool call. That pattern creates approval fatigue and turns review into button-clicking. The product direction is skill-first and CLI-backed: reusable agent skills guide normal work, while the local Patchrail engine records evidence and keeps final approval human-owned.

## Current Alpha Status

`v0.2.0-alpha.1` implements the local contract foundation for this thesis: Brief Schema v1, Runner Contract v1, Evidence Bundle v1, read-side contract inspection, runner-local artifact collection, verification records, review queue, approval packet rendering/export, guided Delivery Contract scaffolds, and the first `patchrail-supervise` skill scaffold.

`ApprovalProfile v1` and `RunLedger v1` are next implementation targets, not completed runtime features in this alpha.

## Target In Scope

- CLI commands for setup bootstrap, config bootstrap, preflight inspection, task creation, Delivery Contract scaffolding through existing planning brief storage, planning, execution, verification, packet export, review-queue listing, status, review, approval, rejection, logs, and artifact lookup.
- A CLI onboarding shell via `patchrail start`, with `patchrail start --once` as the non-interactive splash path.
- A portable Agent Skills distribution path, beginning with a `patchrail-supervise` skill that can be used from Codex, Claude Code, Grok Build, and other clients that understand the `SKILL.md` standard.
- Filesystem persistence under `.patchrail/` or `PATCHRAIL_HOME`.
- CLI-visible workflow backend selection persisted under local config, with `local` as default and `langgraph` as an optional backend.
- Role ontology for `planner`, `reviewer`, and `executor` across `codex`, `claude`, and `grok` with `api` and `subscription` access modes.
- Supervised `plan --auto` and `review --auto` paths behind a pluggable workflow backend seam, with canonical records still owned by Patchrail.
- Deterministic local harness execution through shell-backed commands, with policy-resolved candidates supplying the concrete command.
- Artifact bundle persistence from day one.
- Verification record persistence for command, cwd, exit code, stdout/stderr output paths, elapsed time, task id, and run id.
- Approval packet generation as a read model rather than a new lifecycle entity.
- Local policy config plus persisted `ResolvedAssignment`, `PreflightResult`, and `FallbackEvent` data in plan, review, and run records.
- Decision trace and approval ledger persistence.
- Minimal tests covering happy path, invalid transitions, role-policy resolution, verification, packet rendering, and resumption from disk.

## Target Acceptance Criteria

- `patchrail config init` creates a local role-policy document and persists the selected workflow backend.
- `patchrail setup` bootstraps runtime config, reports preflight status, and returns concrete next commands.
- `patchrail setup project --guided` creates or reuses a task and writes editable local Delivery Contract prompts for Future Completion, Ontology, and Product brief scaffolds.
- `patchrail brief validate` reports required brief sequence readiness without mutating task state.
- `patchrail contracts runner` exposes the read-only Runner Contract v1 handoff.
- `patchrail plan` resolves and persists a planner assignment, stores a plan, and moves the task to `planned`.
- `patchrail run` requires an existing plan, resolves and persists an executor assignment, stores a run, writes artifact files plus invocation metadata, creates an isolated workspace, and moves the task to `review_pending`.
- `patchrail verify --run-id <run_id> --command "<shell command>"` runs an operator-specified verification command, stores stdout/stderr artifacts, records exit code and elapsed time, and does not mutate the canonical task lifecycle.
- `patchrail list verifications` filters verification records by task or run.
- `patchrail list review-queue` groups tasks by missing verification, failed verification, review readiness, approval readiness, and approved state.
- `patchrail packet show|export` renders Markdown or JSON approval packets from existing local records and surfaces unresolved gaps.
- `patchrail review` requires a completed run, resolves and persists a reviewer assignment, stores the verdict and rationale, and moves the task to `awaiting_approval`.
- `patchrail approve` and `patchrail reject` require a completed review and store human rationale plus ledger entries. This final human decision is about accepting the outcome and evidence, not rubber-stamping every intermediate tool call.
- Future sessions can resume by reading the stored files without in-memory context.

## Out Of Scope

- Autonomous final approvals, autonomous merges, or deployment automation.
- A skill-only security model. Skills can guide agent behavior, but enforcement and auditability must remain backed by local policy, hooks, sandbox settings, CLI records, and host-agent permission systems.
- Replacing Codex, Claude Code, or Grok Build native approval/sandbox modes. Patchrail should integrate with those surfaces and record their effective policy instead of pretending to own all enforcement.
- Manual approval prompts for every low-risk file edit or local command.
- LangGraph-driven executor orchestration or backend-owned approval state.
- LangGraph Studio or any dashboard-first operator workflow.
- Full localization of every CLI message beyond the current structured-output discipline.
- Infrastructure automation beyond a placeholder hook contract.

## MVP Discipline

- Choose inspectability over abstraction.
- Prefer one clear path through the workflow over broad autonomous branching.
- Reduce approval fatigue by shifting human judgment to scope setup, risk escalations, verification evidence, and final review.
- Keep saved data language-neutral even if CLI notices become bilingual later.
- Avoid schema churn until the local state flow feels stable under repeated use.
