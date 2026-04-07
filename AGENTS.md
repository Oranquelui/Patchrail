# AGENTS

## Thesis
Patchrail is a local-first, supervised coding-agent control plane for serious users of agentic coding workflows. It exists to make planning, execution, review, approval, and continuation auditable and reproducible without drifting into a generic assistant platform.

## Product Boundaries
- Optimize for CLI-first and headless-core-first workflows.
- Preserve clear role separation between supervisor, executors, and human approver.
- Treat approval boundaries, artifacts, and decision traces as first-class data.
- Keep provider roles distinct; do not flatten everything into a generic model wrapper.
- Prefer the smallest implementation that preserves the thesis.

## Non-Goals
- No chat UI or dashboard-first experience in this phase.
- No broad multi-provider abstraction layer beyond bounded runner interfaces.
- No billing, marketplace, no-code builder, or SaaS platform behavior.
- No speculative infra control center; future infra support is hook-based only.

## Role Separation
- `Codex`: supervisor, planner, reviewer, merge judge.
- `claude_code`: repo-native executor abstraction.
- `grok_runner`: alternate executor abstraction.
- `human`: final approval authority for meaningful state transitions.

## Working Rules
- Human approval is required for meaningful state changes such as final approval or rejection.
- Every plan, run, review, approval, and artifact-producing action must leave a local trace.
- State transitions must be explicit and validated; no silent implicit progress.
- Persist enough local state for a future session to resume safely from disk alone.
- Keep runner integrations replaceable, but do not over-generalize the runner interface.

## Coding Conventions
- Use Python 3.12+ compatible code and avoid 3.14-only features.
- Keep modules small and responsibility-focused.
- Prefer stdlib unless a dependency clearly reduces core complexity.
- Treat filesystem persistence as a product surface: readable, stable, and inspectable.
- Write tests for behavior before adding production logic for that behavior.
- Do not hide side effects behind convenience helpers; make storage and transitions obvious.

## State Discipline
- Task lifecycle: `created -> planned -> running -> review_pending -> awaiting_approval -> approved|rejected`.
- Run, review, and approval records are separate entities and must remain queryable independently.
- Review records store verdict plus rationale.
- Approval records store the human decision plus rationale and ledger entry.
- Artifact bundles are immutable outputs of a run and must be stored from day one.

## Safe Continuation
1. Read this file and `docs/mvp.md` before changing scope.
2. Inspect `.patchrail/` storage layout and existing ledgers before changing data models.
3. Preserve CLI-first behavior; add UI surfaces only after the headless core is stable.
4. Extend runner integrations behind the existing runner contract instead of leaking provider logic into core services.
5. Update `docs/architecture.md` and `docs/backlog.md` whenever module boundaries or continuation priorities change.
6. Keep deferred work deferred unless it unblocks the current milestone directly.
