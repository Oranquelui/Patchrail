# Patchrail Backlog

## Next Milestones
1. Replace the remaining shell/local-harness execution paths with a real `codex` subscription adapter while keeping the current role-policy contract stable. Claude subscription is now live. Grok remains API-only until its subscription contract is safe enough for supervision.
2. Expand the optional workflow backend seam beyond the default local backend: deepen the LangGraph planner path, add a richer reviewer workflow, and extend `plan --auto` / `review --auto` without moving canonical records out of Patchrail.
3. Promote isolated run workspaces from simple manifest folders into real execution sandboxes with stronger provenance and an explicit runner path contract for task, plan, output, artifacts, and trace handoff.
4. Capture richer diffs, review summaries, manifest-style artifact metadata, and optional structured runner traces from executor outputs.
5. Add richer filters and history views on top of the current list surface so the local store stays usable as record volume grows.
6. Add finer-grained approval policies such as time-bounded fallback approvals and role-specific approvers.

## Deferred Features
- Dashboard or browser-based review UI.
- Harbor-style task or dataset registry, package publishing, or distribution workflow.
- Job or trial bulk evaluation orchestration across remote runtimes.
- Generic provider marketplace behavior.
- Billing, quotas, or cloud tenancy concerns.
- Autonomous merges or approvals.
- Multi-user coordination or remote sync.
- Infra control center behavior beyond hook contracts.
- Full bilingual CLI surface beyond the current structured JSON and English error baseline.

## Continuation Queue
1. Introduce a real `codex_subscription` executor behind the existing role-policy contract, or keep it deferred if the non-interactive runtime path remains unstable.
2. Introduce live `review --auto` support for additional candidates once a safe reviewer runtime exists beyond `claude api`, while keeping reviewer verdicts subordinate to Patchrail's canonical records.
3. Promote the optional `langgraph` backend from single-pass planner/reviewer scaffolding into richer subordinate workflow state without handing over approval, ledger, or artifact ownership.
4. Introduce real diff ingestion plus manifest-style artifact metadata with digests, logical kinds, and collection status so review results can reference concrete outputs.
5. Define an optional runner trace schema for supervised Patchrail runs, borrowing the useful parts of Harbor-style trajectory data without drifting into a generic eval or RL format.
6. Formalize the runner workspace path contract and reserved environment variables for task, plan, output, artifact, and trace exchange.
7. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
8. Add richer list filters and historical views for large local stores.
9. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review
- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path for both `local` and `real` presets, a first role ontology with local and real role-policy presets, provider-aware preflight checks, executor API runners with explicit `--access-mode api` selection, a Claude subscription executor runner, a workflow-engine seam for auto-generated `plan --auto` and `review --auto` flows, an optional LangGraph backend scaffold, an explicit fallback approval request path, standalone preflight snapshots, and list-oriented CLI navigation for the main local records.
- The next session should preserve the current ontology and approval boundaries while improving workflow backends, real provider adapters, provenance, richer read-side filtering, and structured run artifacts instead of drifting toward benchmark-registry or evaluation-framework scope.
