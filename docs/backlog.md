# Patchrail Backlog

## Next Milestones
1. Harden `patchrail verify`, `patchrail list review-queue`, and `patchrail packet show|export` as the v0.2 portfolio surface for AI coding verification.
2. Add richer verification presets and command groups while keeping commands operator-specified and locally auditable.
3. Improve approval packets with diff summaries, verification grouping, and clearer unresolved-gap explanations.
4. Expand the Delivery Contract setup path beyond the first guided brief artifact templates without changing the canonical state machine.
5. Add triangulated planning inputs across `Codex / OpenAI`, `Claude`, and `Grok`, keeping their roles distinct and storing only Patchrail-owned canonical plan output plus companion planning artifacts or metadata.
6. Expand the optional workflow backend seam beneath that planning layer: deepen the LangGraph planner path, add a richer reviewer workflow, and extend `plan --auto` / `review --auto` without moving canonical records out of Patchrail.
7. Promote isolated run workspaces from simple manifest folders into real execution sandboxes with stronger provenance and an explicit runner path contract for task, plan, output, artifacts, verification, and trace handoff.
8. Capture richer diffs and review summaries from executor outputs, building on the current manifest-style artifact metadata, verification records, and initial structured runner trace support.
9. Build on the new artifact-bundle, verification, and review-queue views with richer filters and history surfaces so the local store stays usable as record volume grows.
10. Add finer-grained approval policies such as time-bounded fallback approvals and role-specific approvers.
11. Evolve the runner trace schema beyond the current `trace.json` payload without drifting into a generic eval framework.

## Deferred Features
- Dashboard or browser-based review UI.
- Harbor-style task or dataset registry.
- Job or trial bulk evaluation orchestration across remote runtimes.
- Generic provider marketplace behavior.
- Billing, quotas, or cloud tenancy concerns.
- Autonomous merges or approvals.
- Multi-user coordination or remote sync.
- Infra control center behavior beyond hook contracts.
- Full bilingual CLI surface beyond the current human-readable default output, explicit `--json` automation mode, and English error baseline.

## Continuation Queue
1. Add a smoke flow that demonstrates `task -> plan -> run -> verify -> review -> approve -> packet export`.
2. Decide whether `patchrail start` should remain a shell launcher or delegate first-run users into the `patchrail setup` runtime/project path.
3. Add explicit packet sections for changed files and diff evidence after real diff ingestion lands.
4. Promote guided Delivery Contract capture beyond templates while keeping the existing `brief` records for compatibility.
5. Add triangulated planner candidate generation and comparison so Patchrail can record why the canonical plan was chosen rather than just which backend produced it.
6. Promote the optional `langgraph` backend from planner/reviewer scaffolding into richer subordinate workflow state without handing over approval, ledger, or artifact ownership.
7. Evolve the current optional runner trace schema beyond the MVP `trace.json` payload, borrowing the useful parts of Harbor-style trajectory data without drifting into a generic eval or RL format.
8. Formalize the runner workspace path contract and reserved environment variables for task, plan, output, artifact, verification, and trace exchange.
9. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
10. Add richer list filters and historical views for large local stores beyond the current artifact-bundle, verification, and task-scoped read-side queries.
11. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review
- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path for both `local` and `real` presets, a first role ontology with local and real role-policy presets, provider-aware preflight checks, executor API runners with explicit `--access-mode api` selection, live Claude and Codex subscription executor runners, live Codex subscription reviewer automation, a workflow-engine seam for auto-generated `plan --auto` and `review --auto` flows, an optional LangGraph backend scaffold, manifest-style artifact metadata with digests and logical kinds, an initial optional `trace.json` runner artifact, an explicit fallback approval request path, standalone preflight snapshots, verification records, approval packet read models, review-queue grouping, list-oriented CLI navigation for the main local records including artifact-bundle and verification history, `setup`/`start`/`doctor` onboarding commands, a minimal interactive `patchrail start` shell for TTY sessions, human-readable default CLI output with explicit `--json` automation mode, and a guided Delivery Contract template path attached to canonical plan records through existing brief storage.
- The next session should preserve the current ontology and approval boundaries while improving verification presets, packet evidence quality, guided Delivery Contract capture, and public distribution checks before broadening executor sophistication.
