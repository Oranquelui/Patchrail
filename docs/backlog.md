# Patchrail Backlog

## Next Milestones

1. Add `ApprovalProfile v1` and `RunLedger v1` so Patchrail reduces approval fatigue by distinguishing low-risk auto-approved actions from boundary-crossing escalations and denials.
2. Validate and harden the first portable `patchrail-supervise` Agent Skill using realistic Codex, Claude Code, and Grok Build supervision scenarios.
3. Package the skill for Codex as a plugin once the local skill is stable, keeping the CLI as the canonical local state engine and the skill/plugin as the distribution surface.
4. Improve verification presets and packet evidence quality so approval packets can summarize changed files, diff evidence, verification results, and unresolved gaps more clearly.
5. Promote guided Delivery Contract capture beyond templates while keeping the existing `brief` records for compatibility.
6. Capture effective native agent approval settings where possible, such as Codex approval/sandbox mode, Claude permission mode, or Grok plugin/hook configuration.
7. Add triangulated planning inputs across `Codex / OpenAI`, `Claude`, and `Grok`, keeping their roles distinct and storing only Patchrail-owned canonical plan output plus companion planning artifacts or metadata.
8. Expand the optional workflow backend seam beneath that planning layer without moving canonical records out of Patchrail.
9. Promote isolated run workspaces beyond Runner Contract v1 into stronger execution sandboxes with runner trace validation.
10. Build richer list filters and history surfaces for artifact bundles, verification records, packets, and task-scoped review queues.
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
4. Teach the skill to prefer policy setup, scope confirmation, verification evidence, and final review over repeated per-command approval prompts as `ApprovalProfile v1` becomes executable.
5. Improve approval packet sections for changed files and diff evidence after real diff ingestion lands.
6. Add verification presets for common Python, Node, and shell workflows.
7. Promote `patchrail setup project --guided` from scaffold generation into guided capture for existing `future`, `ontology`, and `product` planning brief artifacts plus approval-profile selection.
8. Decide whether `patchrail start` should remain a shell launcher or delegate first-run users into the `patchrail setup` runtime/project/approval-profile path.
9. Add triangulated planner candidate generation and comparison so Patchrail can record why the canonical plan was chosen rather than just which backend produced it.
10. Promote the optional `langgraph` backend from planner/reviewer scaffolding into richer subordinate workflow state without handing over approval, ledger, artifact, verification, or packet ownership.
11. Add Runner Contract v1 validation for runner-local artifact size, naming, and media-type limits now that basic artifact ingestion is canonicalized.
12. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
13. Add richer list filters and historical views for large local stores beyond the current artifact-bundle, verification, packet, and task-scoped read-side queries.
14. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review

- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path for both `local` and `real` presets, a first role ontology with local and real role-policy presets, provider-aware preflight checks, executor API runners with explicit `--access-mode api` selection, live Claude and Codex subscription executor runners, live Codex subscription reviewer automation, a workflow-engine seam for auto-generated `plan --auto` and `review --auto` flows, an optional LangGraph backend scaffold, Evidence Bundle v1 manifest metadata, Runner Contract v1 workspace and reserved environment boundaries, canonical collection of runner-local artifacts, verification records, approval packet read models, review-queue grouping, `setup`/`start`/`doctor` onboarding commands, a minimal interactive `patchrail start` shell, human-readable default CLI output with explicit `--json` automation mode, and a guided Delivery Contract template path attached to canonical plan records through existing brief storage.
- The next session should preserve the current ontology and approval boundaries while shifting from CLI-only supervision toward skill-first, CLI-backed, risk-aware delegation. The immediate focus is `ApprovalProfile v1`, `RunLedger v1`, `patchrail-supervise` validation, and approval-packet evidence quality before broadening executor sophistication.
