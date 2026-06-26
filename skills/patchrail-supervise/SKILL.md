---
name: patchrail-supervise
description: Use when supervising coding-agent work with Patchrail, preparing a Patchrail task, running a Patchrail-controlled executor, reviewing evidence, or deciding whether a task can move toward human approval.
---

# Patchrail Supervise

Patchrail is the local source of truth. Use the CLI for state, evidence, and approvals; use this skill only to guide the agent workflow.

## Workflow

1. Confirm the repository root and inspect `AGENTS.md`, `README.md`, and `docs/mvp.md` when they exist.
2. Bootstrap local config with `patchrail setup` or inspect readiness with `patchrail doctor`.
3. Create project scaffolds with `patchrail setup project --title "<title>" --description "<description>"`.
4. Have the human or operator-facing agent fill in the generated `future`, `ontology`, and `product` briefs.
5. Persist each brief with `patchrail brief create --task-id <task_id> --kind <future|ontology|product> --file <path>`.
6. Run `patchrail brief validate --task-id <task_id>` before planning.
7. Inspect executor handoff with `patchrail contracts runner` when runner behavior matters.
8. Create or generate the plan with `patchrail plan --task-id <task_id>` or `patchrail plan --task-id <task_id> --auto`.
9. Execute with `patchrail run --task-id <task_id> --runner auto` unless the operator chose a specific runner.
10. Review evidence with `patchrail status --task-id <task_id>`, `patchrail artifacts --run-id <run_id>`, and `patchrail list artifact-bundles --task-id <task_id>`.
11. Do not approve or reject the final outcome without explicit human instruction.

## Approval Fatigue Rule

Prefer one clear scope and policy decision before work over repeated low-value prompts during work. Until `ApprovalProfile v1` exists, record the requested delegation boundary in the planning briefs or plan summary, and escalate these classes explicitly:

- dependency installation or lockfile changes
- CI, auth, deployment, database, or production API changes
- broad network access or external comments
- branch pushes, PR creation, merges, or releases
- destructive filesystem commands or work outside the repository
- any action involving secrets or credentials

Routine repository reads, scoped edits, local tests, lint, type checks, formatters, and writes to Patchrail artifact directories may proceed only when the host agent permission mode and the operator's stated scope allow them.

## Hard Boundaries

- Skill instructions are not the enforcement layer.
- Do not bypass the host agent's sandbox, approval mode, or permission system.
- Do not claim Patchrail approved work just because a tool command succeeded.
- Do not let a runner own canonical task state, plans, reviews, approvals, ledgers, or evidence bundle meaning.
- Do not approve or reject the final outcome without explicit human instruction.

## Completion Evidence

Before saying the supervised task is ready for human approval, collect:

- task id, plan id, run id, review id when present
- brief validation result
- runner contract version when relevant
- evidence bundle schema version
- test or smoke command output
- final diff summary
- unresolved escalation or denial notes
