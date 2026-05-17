# Patchrail Supervised Agent Rollout Case Study

## Customer / Domain
Patchrail is framed for enterprise engineering teams that want to introduce AI coding agents inside customer environments without losing supervision, approval boundaries, or local audit evidence.

## Problem
AI coding agents can move from vague intent to repository changes quickly, but client work often needs stronger controls before execution starts. Operators need to define what finished means, which concepts are real, where ownership and approval boundaries sit, and what scope is explicitly out of bounds. They also need the resulting plan, run, review, approval, logs, artifacts, and decision traces to remain inspectable from disk.

## Constraints
- CLI-first and headless-core-first operation.
- No dashboard-first workflow in this phase.
- Local-first persistence under `.patchrail/` or `PATCHRAIL_HOME`.
- No second canonical state machine beyond `Task -> Plan -> Run -> ReviewResult -> ApprovalRecord`.
- Human approval for meaningful completion decisions.
- Provider roles remain distinct instead of being flattened into one generic model wrapper.
- Browser-control MCPs are not globally registered, do not use `--autoConnect`, and are not part of startup configuration.

## Architecture
Patchrail uses a thin `argparse` CLI over a local service layer and filesystem store. The canonical workflow remains `Task`, `Plan`, `Run`, `ReviewResult`, and `ApprovalRecord`, with decision and approval ledgers stored as JSONL.

The Phase 1 planning layer adds three companion artifacts before execution:

| Layer | Artifact | Purpose |
| --- | --- | --- |
| Prediction | `Future Completion Brief` | Predict what should be true in the future before any executor runs. |
| Reality boundary | `Ontology Brief` | Define what exists, who owns it, and where approval/artifact boundaries sit. |
| Post-implementation acceptance | `Product Brief` | Define what must be true after implementation for users and operators. |

The harness then acts as the post-implementation evidence layer. It does not own canonical state; it captures execution summary, diff summary, stdout/stderr, invocation metadata, runner trace, and artifact metadata after the executor runs and before review.

These briefs are stored as local JSON companion artifacts under `.patchrail/briefs/`. When `patchrail plan` creates the canonical plan, it records stable `planning_briefs` references containing the brief id, kind, source path, storage path, digest, and creation timestamp. The plan remains the canonical planning record; briefs are supporting artifacts.

## Security Decisions
- Briefs are local files copied into Patchrail-owned storage with SHA-256 digests.
- Approval and rejection remain explicit human actions after review.
- Fallback across provider or access-mode boundaries is blocked until a fallback approval is recorded.
- Runners receive serialized task and plan inputs in isolated per-run workspaces.
- Artifact bundles persist stdout, stderr, execution summary, diff summary, invocation metadata, and optional runner traces locally.
- No browser dashboard, no global Browser MCP registration, and no `file://` output is required for this workflow.

## Implementation
The current implementation adds:

- `patchrail setup` for first-run runtime bootstrap and preflight-oriented next steps.
- `patchrail setup project --title ... --description ...` for task creation plus editable local planning brief scaffolds.
- `patchrail brief create --task-id ... --kind future|ontology|product --file ...` after replacing scaffold placeholders with concrete planning content.
- `patchrail brief list --task-id ...`
- `patchrail brief show --brief-id ...`
- Plan serialization with `planning_briefs`.
- Auto planner prompt context that can include the stored planning briefs.
- Local JSON storage for brief companion artifacts.
- Tests covering creation, list/show, invalid kind rejection, missing task rejection, plan reference behavior, status, run, and logs.

## Operations
A local operator can run the controlled path as:

```bash
patchrail setup
patchrail setup project --title "Client agent rollout" --description "Introduce supervised coding agents"
# edit generated future/ontology/product source files, then persist them
patchrail brief create --task-id <task_id> --kind future --file <future_brief_file>
patchrail brief create --task-id <task_id> --kind ontology --file <ontology_brief_file>
patchrail brief create --task-id <task_id> --kind product --file <product_brief_file>
patchrail plan --task-id <task_id> --summary "Execute within explicit planning boundaries" --step "Read briefs" --step "Run bounded implementation"
patchrail run --task-id <task_id> --runner claude_code
patchrail review --run-id <run_id> --verdict pass --summary "Reviewed persisted artifacts"
patchrail approve --task-id <task_id> --rationale "Meets the agreed completion boundary"
```

Read-side inspection stays local:

```bash
patchrail brief list --task-id <task_id>
patchrail brief show --brief-id <brief_id>
patchrail status --task-id <task_id>
patchrail logs --run-id <run_id>
patchrail artifacts --run-id <run_id>
```

## Evidence
The local store contains:

- `.patchrail/tasks/<task_id>.json`
- `.patchrail/briefs/<brief_id>.json`
- `.patchrail/plans/<plan_id>.json`
- `.patchrail/runs/<run_id>.json`
- `.patchrail/reviews/<review_id>.json`
- `.patchrail/approvals/<approval_id>.json`
- `.patchrail/artifacts/<run_id>/bundle.json`
- `.patchrail/ledgers/decision-trace.jsonl`
- `.patchrail/ledgers/approval-ledger.jsonl`

The test suite verifies the new brief layer and the existing major CLI flow. The first brief-layer test creates a brief, lists and shows it, creates a plan that references it, runs the local harness, and reads logs from the persisted run.

## Outcome
Patchrail can now be described as a local-first, approval-gated, evidence-preserving CLI control plane for introducing AI coding agents at customer sites. It helps a customer-facing technical operator show how completion definition, ontology boundaries, and product scope become explicit before execution, then remain connected to the plan, run, review, approval, ledgers, and artifacts on disk.

Current limits are deliberate: there is no dashboard, no autonomous approval, and no Codex/Claude/Grok triangulated planning path yet. The first delivered layer is the deterministic local planning brief path that the later triangulation layer can consume.
