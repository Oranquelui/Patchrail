# Patchrail Backlog

## Next Milestones
1. Replace the remaining shell/local-harness execution paths with a real `codex` subscription adapter while keeping the current role-policy contract stable. Claude subscription is now live. Grok remains API-only until its subscription contract is safe enough for supervision.
2. Expand the optional workflow backend seam beyond the default local backend: deepen the LangGraph planner path, add a richer reviewer workflow, and extend `plan --auto` / `review --auto` without moving canonical records out of Patchrail.
3. Promote isolated run workspaces from simple manifest folders into real execution sandboxes with stronger provenance and an explicit runner path contract for task, plan, output, artifacts, and trace handoff.
4. Capture richer diffs and review summaries from executor outputs, building on the current manifest-style artifact metadata and initial structured runner trace support.
5. Build on the new artifact-bundle history view with richer filters and history surfaces so the local store stays usable as record volume grows.
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
4. Introduce real diff ingestion so review results can reference concrete outputs instead of summary-only placeholders.
5. Evolve the current optional runner trace schema beyond the MVP `trace.json` payload, borrowing the useful parts of Harbor-style trajectory data without drifting into a generic eval or RL format.
6. Formalize the runner workspace path contract and reserved environment variables for task, plan, output, artifact, and trace exchange.
7. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
8. Add richer list filters and historical views for large local stores beyond the current artifact-bundle and task-scoped read-side queries.
9. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review
- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path for both `local` and `real` presets, a first role ontology with local and real role-policy presets, provider-aware preflight checks, executor API runners with explicit `--access-mode api` selection, a Claude subscription executor runner, a workflow-engine seam for auto-generated `plan --auto` and `review --auto` flows, an optional LangGraph backend scaffold, manifest-style artifact metadata with digests and logical kinds, an initial optional `trace.json` runner artifact, an explicit fallback approval request path, standalone preflight snapshots, and list-oriented CLI navigation for the main local records including artifact-bundle history.
- The next session should preserve the current ontology and approval boundaries while improving workflow backends, real provider adapters, diff ingestion, richer read-side filtering, and deeper runner traces instead of drifting toward benchmark-registry or evaluation-framework scope.
