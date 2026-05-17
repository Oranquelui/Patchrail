# Patchrail Backlog

## Next Milestones
1. Expand the Phase 1 planning layer beyond the first brief artifact path: split onboarding into `machine/runtime onboarding` and `project/planning onboarding`, and guide the `Future Completion Brief -> Ontology Brief -> Product Brief -> Plan` sequence without changing the canonical state machine.
2. Add triangulated planning inputs across `Codex / OpenAI`, `Claude`, and `Grok`, keeping their roles distinct and storing only Patchrail-owned canonical plan output plus companion planning artifacts or metadata.
3. Expand the optional workflow backend seam beneath that planning layer: deepen the LangGraph planner path, add a richer reviewer workflow, and extend `plan --auto` / `review --auto` without moving canonical records out of Patchrail.
4. Promote isolated run workspaces from simple manifest folders into real execution sandboxes with stronger provenance and an explicit runner path contract for task, plan, output, artifacts, and trace handoff.
5. Capture richer diffs and review summaries from executor outputs, building on the current manifest-style artifact metadata and initial structured runner trace support.
6. Build on the new artifact-bundle history view with richer filters and history surfaces so the local store stays usable as record volume grows.
7. Add finer-grained approval policies such as time-bounded fallback approvals and role-specific approvers.
8. Evolve the runner trace schema beyond the current `trace.json` payload without drifting into a generic eval framework.

## Deferred Features
- Dashboard or browser-based review UI.
- Harbor-style task or dataset registry, package publishing, or distribution workflow.
- Job or trial bulk evaluation orchestration across remote runtimes.
- Generic provider marketplace behavior.
- Billing, quotas, or cloud tenancy concerns.
- Autonomous merges or approvals.
- Multi-user coordination or remote sync.
- Infra control center behavior beyond hook contracts.
- Full bilingual CLI surface beyond the current human-readable default output, explicit `--json` automation mode, and English error baseline.

## Continuation Queue
1. Promote `patchrail setup project` from scaffold generation into guided capture for the existing `future`, `ontology`, and `product` planning brief artifacts.
2. Decide whether `patchrail start` should remain a shell launcher or delegate first-run users into the `patchrail setup` runtime/project path.
3. Add triangulated planner candidate generation and comparison so Patchrail can record why the canonical plan was chosen rather than just which backend produced it.
4. Promote the optional `langgraph` backend from planner/reviewer scaffolding into richer subordinate workflow state without handing over approval, ledger, or artifact ownership.
5. Introduce real diff ingestion so review results can reference concrete outputs instead of summary-only placeholders.
6. Evolve the current optional runner trace schema beyond the MVP `trace.json` payload, borrowing the useful parts of Harbor-style trajectory data without drifting into a generic eval or RL format.
7. Formalize the runner workspace path contract and reserved environment variables for task, plan, output, artifact, and trace exchange.
8. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
9. Add richer list filters and historical views for large local stores beyond the current artifact-bundle and task-scoped read-side queries.
10. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review
- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path for both `local` and `real` presets, a first role ontology with local and real role-policy presets, provider-aware preflight checks, executor API runners with explicit `--access-mode api` selection, live Claude and Codex subscription executor runners, live Codex subscription reviewer automation, a workflow-engine seam for auto-generated `plan --auto` and `review --auto` flows, an optional LangGraph backend scaffold, manifest-style artifact metadata with digests and logical kinds, an initial optional `trace.json` runner artifact, an explicit fallback approval request path, standalone preflight snapshots, list-oriented CLI navigation for the main local records including artifact-bundle history, `setup`/`start`/`doctor` onboarding commands, a minimal interactive `patchrail start` shell for TTY sessions, human-readable default CLI output with explicit `--json` automation mode, and a first local planning brief artifact layer attached to canonical plan records.
- The next session should preserve the current ontology and approval boundaries while improving guided editing for future-anchored planning, dual-pass onboarding, and triangulated multi-provider plan generation before broadening executor sophistication or read-side surfaces.
