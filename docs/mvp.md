# Patchrail MVP

## Goal
Prove Patchrail’s revised thesis with the narrowest useful supervised workflow: an operator can define task intent, scope, risk policy, and completion evidence once, then let Codex, Claude Code, Grok Build, or another compatible coding agent work with low-friction local autonomy while Patchrail preserves the policy, run ledger, artifacts, escalations, final approval decision, and safe continuation state on disk.

Patchrail is not trying to make humans approve every tool call. That pattern creates approval fatigue and turns review into button-clicking. The MVP direction is skill-first and CLI-backed: reusable agent skills guide the coding agent in normal work, while the local Patchrail engine records evidence, classifies risk, and escalates only actions that cross explicit boundaries.

## Current Alpha Status
`v0.2.0-alpha.1` implements the local contract foundation for this revised thesis: Brief Schema v1, Runner Contract v1, Evidence Bundle v1, read-side contract inspection, runner-local artifact collection, and the first `patchrail-supervise` skill scaffold. `ApprovalProfile v1` and `RunLedger v1` are the next implementation targets, not completed runtime features in this alpha.

## Target In Scope
- CLI commands for setup bootstrap, config bootstrap, preflight inspection, task creation, planning brief scaffolding, planning, execution, status, review, approval, rejection, logs, and artifact lookup.
- A CLI onboarding shell via `patchrail start`, with `patchrail start --once` as the non-interactive splash path.
- A portable Agent Skills distribution path, beginning with a `patchrail-supervise` skill that can be used from Codex, Claude Code, Grok Build, and other clients that understand the `SKILL.md` standard.
- A CLI-backed engine that skills and future plugins can call for local persistence, evidence capture, policy inspection, and read-side reconstruction.
- Filesystem persistence under `.patchrail/` or `PATCHRAIL_HOME`.
- CLI-visible workflow backend selection persisted under local config, with `local` as default and `langgraph` as an optional backend.
- Role ontology for `planner`, `reviewer`, and `executor` across `codex`, `claude`, and `grok` with `api` and `subscription` access modes.
- Supervised `plan --auto` and `review --auto` paths behind a pluggable workflow backend seam, with canonical records still owned by Patchrail.
- Approval profiles that distinguish low-risk auto-approved work from boundary-crossing escalations. Routine repository reads, scoped edits, local tests, linters, type checks, and artifact writes should not require repeated human approval.
- Explicit escalation records for higher-risk actions such as dependency installation, lockfile changes, CI/auth/deployment changes, network access, external comments, branch pushes, production API use, and destructive shell commands.
- Run ledger persistence that records granted scope, auto-approved action classes, escalations, denials, receipts, and rollback notes.
- Deterministic local harness execution through shell-backed commands, with policy-resolved candidates supplying the concrete command.
- Artifact bundle persistence from day one.
- Per-run isolated workspaces containing task, plan, and runner output manifests.
- A repo-local smoke path via `scripts/local_smoke_test.sh` and `patchrail.runners.local_harness`.
- Local policy config plus persisted `ResolvedAssignment`, `PreflightResult`, and `FallbackEvent` data in plan, review, and run records.
- Decision trace and approval ledger persistence.
- Minimal tests covering happy path, invalid transitions, role-policy resolution, and resumption from disk.

## Target Acceptance Criteria
- `patchrail config init` creates a local role-policy document and persists the selected workflow backend.
- `patchrail config init` can create or select an approval profile that defines auto, ask, and deny action classes without requiring per-tool manual approval.
- `patchrail setup` bootstraps runtime config, reports preflight status, and returns concrete next commands.
- `patchrail setup` explains the skill-first path and the CLI-backed path so operators can use Patchrail from their preferred coding agent or directly from the terminal.
- `patchrail setup project` creates or reuses a task and writes editable local Future Completion, Ontology, and Product brief scaffolds; operators persist edited brief content with `patchrail brief create` before plan creation.
- `patchrail start` can bootstrap config and keep an operator in a TTY shell without introducing a second canonical state model.
- `patchrail preflight` reports role candidate readiness from local state and environment only.
- A `patchrail-supervise` Agent Skill can guide an agent through task scope, approval profile selection, run evidence expectations, escalation criteria, and final review without requiring the user to paste the same supervision instructions repeatedly.
- `patchrail task create` creates a task and persists it locally.
- `patchrail plan` resolves and persists a planner assignment, stores a plan, and moves the task to `planned`.
- `patchrail plan --auto` routes through the configured workflow backend without changing Patchrail's canonical plan record ownership.
- `patchrail run` requires an existing plan, resolves and persists an executor assignment, stores a run, writes artifact files plus invocation metadata, creates an isolated workspace, records the effective approval profile, and moves the task to `review_pending`.
- `patchrail run` records which action classes were allowed automatically and which actions required escalation or denial.
- `patchrail review` requires a completed run, resolves and persists a reviewer assignment, stores the verdict and rationale, and moves the task to `awaiting_approval`.
- `patchrail review --auto` routes through the configured workflow backend without changing approval, ledger, or artifact ownership.
- `patchrail approve` and `patchrail reject` require a completed review and store human rationale plus ledger entries. This final human decision is about accepting the outcome and evidence, not rubber-stamping every intermediate tool call.
- Cross-provider or cross-access-mode fallback is blocked until additional approval exists.
- `patchrail status`, `patchrail logs`, and `patchrail artifacts` reconstruct output entirely from persisted local state.
- Future sessions can resume by reading the stored files without in-memory context.

## Out Of Scope
- Real provider SDK integrations.
- Background workers or distributed execution.
- Worktree management beyond future runner needs.
- Web dashboards or GUI review surfaces.
- Unbounded fully autonomous planning/execution, autonomous final approvals, or merge automation.
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
- Reduce approval fatigue by shifting human judgment to scope setup, risk escalations, and final evidence review.
- Keep saved data language-neutral even if CLI notices become bilingual later.
- Avoid schema churn until the local state flow feels stable under repeated use.
