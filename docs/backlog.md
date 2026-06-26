# Patchrail Backlog

## Next Milestones
1. Add `ApprovalProfile v1` and `RunLedger v1` so Patchrail reduces approval fatigue by distinguishing low-risk auto-approved actions from boundary-crossing escalations and denials.
2. Validate and harden the first portable `patchrail-supervise` Agent Skill using realistic Codex, Claude Code, and Grok Build supervision scenarios.
3. Package the skill for Codex as a plugin once the local skill is stable, keeping the CLI as the canonical local state engine and the skill/plugin as the distribution surface.
4. Expand the Phase 1 planning layer beyond the first brief artifact path: split onboarding into `machine/runtime onboarding` and `project/planning onboarding`, and guide the `Future Completion Brief -> Ontology Brief -> Product Brief -> Approval Profile -> Plan` sequence without changing the canonical state machine.
5. Add triangulated planning inputs across `Codex / OpenAI`, `Claude`, and `Grok`, keeping their roles distinct and storing only Patchrail-owned canonical plan output plus companion planning artifacts or metadata.
6. Expand the optional workflow backend seam beneath that planning layer: deepen the LangGraph planner path, add a richer reviewer workflow, and extend `plan --auto` / `review --auto` without moving canonical records out of Patchrail.
7. Promote isolated run workspaces beyond the now-explicit Runner Contract v1 into real execution sandboxes with stronger provenance, runner trace validation, and effective native approval-mode capture.
8. Capture richer diffs and review summaries from executor outputs, building on the Evidence Bundle v1 manifest contract, current artifact metadata, initial structured runner trace support, and run-ledger receipts.
9. Build on the new artifact-bundle history view with richer filters and history surfaces so the local store stays usable as record volume grows.
10. Add finer-grained approval policies such as time-bounded fallback approvals, one-shot escalation grants, and role-specific approvers.
11. Evolve the runner trace schema beyond the current `trace.json` payload without drifting into a generic eval framework.

## Deferred Features
- Dashboard or browser-based review UI.
- Harbor-style task or dataset registry, package publishing, or distribution workflow.
- Job or trial bulk evaluation orchestration across remote runtimes.
- Generic provider marketplace behavior.
- Billing, quotas, or cloud tenancy concerns.
- Autonomous merges or approvals.
- Approval-by-button workflows that ask humans to approve every low-risk edit or local command.
- Multi-user coordination or remote sync.
- Infra control center behavior beyond hook contracts.
- Full bilingual CLI surface beyond the current human-readable default output, explicit `--json` automation mode, and English error baseline.

## Continuation Queue
1. Define `ApprovalProfile v1` with initial `auto`, `ask`, and `deny` action classes for local coding-agent work.
2. Define `RunLedger v1` so every run records the effective approval profile, auto-approved action classes, escalations, denials, receipts, and rollback notes.
3. Validate the first local `patchrail-supervise` skill against realistic supervision prompts before building any broader plugin package.
4. Teach the skill to prefer policy setup, scope confirmation, and final evidence review over repeated per-command approval prompts as `ApprovalProfile v1` becomes executable.
5. Capture effective native agent approval settings where possible, such as Codex approval/sandbox mode, Claude permission mode, or Grok plugin/hook configuration.
6. Promote `patchrail setup project` from scaffold generation into guided capture for the existing `future`, `ontology`, and `product` planning brief artifacts plus approval-profile selection.
7. Decide whether `patchrail start` should remain a shell launcher or delegate first-run users into the `patchrail setup` runtime/project/approval-profile path.
8. Add triangulated planner candidate generation and comparison so Patchrail can record why the canonical plan was chosen rather than just which backend produced it.
9. Promote the optional `langgraph` backend from planner/reviewer scaffolding into richer subordinate workflow state without handing over approval, ledger, or artifact ownership.
10. Introduce real diff ingestion so review results can reference concrete outputs instead of summary-only placeholders.
11. Evolve the current optional runner trace schema beyond the MVP `trace.json` payload, borrowing the useful parts of Harbor-style trajectory data without drifting into a generic eval or RL format.
12. Add Runner Contract v1 validation for runner-local artifact size, naming, and media-type limits now that basic artifact ingestion is canonicalized.
13. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
14. Add richer list filters and historical views for large local stores beyond the current artifact-bundle and task-scoped read-side queries.
15. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review
- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path for both `local` and `real` presets, a first role ontology with local and real role-policy presets, provider-aware preflight checks, executor API runners with explicit `--access-mode api` selection, live Claude and Codex subscription executor runners, live Codex subscription reviewer automation, a workflow-engine seam for auto-generated `plan --auto` and `review --auto` flows, an optional LangGraph backend scaffold, Evidence Bundle v1 manifest metadata with digests and logical kinds, Runner Contract v1 workspace and reserved environment boundaries including a runtime schema-version variable with read-only CLI inspection plus local compatibility trace evidence, canonical collection of runner-local artifacts from the reserved workspace artifact directory, an initial optional `trace.json` runner artifact, an explicit fallback approval request path, standalone preflight snapshots, list-oriented CLI navigation for the main local records including artifact-bundle history, `setup`/`start`/`doctor` onboarding commands, a minimal interactive `patchrail start` shell for TTY sessions, human-readable default CLI output with explicit `--json` automation mode, and a first local planning brief artifact layer attached to canonical plan records.
- The next session should preserve the current ontology and approval boundaries while shifting the product direction from CLI-only supervision toward skill-first, CLI-backed, risk-aware delegation. The immediate focus is `ApprovalProfile v1`, `RunLedger v1`, and a portable `patchrail-supervise` Agent Skill before broadening executor sophistication or read-side surfaces.
