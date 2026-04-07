# Patchrail Backlog

## Next Milestones
1. Replace the remaining shell/local-harness execution paths with a real `codex` subscription adapter while keeping the current role-policy contract stable. Claude subscription is now live. Grok remains API-only until its subscription contract is safe enough for supervision.
2. Extend automated `plan --auto` and `review --auto` beyond the current safe live paths, especially once `codex subscription` becomes trustworthy for supervised review.
3. Promote isolated run workspaces from simple manifest folders into real execution sandboxes with stronger provenance.
4. Capture richer diffs, review summaries, and provenance metadata from runner outputs.
5. Add richer filters and history views on top of the current list surface so the local store stays usable as record volume grows.
6. Add finer-grained approval policies such as time-bounded fallback approvals and role-specific approvers.

## Deferred Features
- Dashboard or browser-based review UI.
- Generic provider marketplace behavior.
- Billing, quotas, or cloud tenancy concerns.
- Autonomous merges or approvals.
- Multi-user coordination or remote sync.
- Infra control center behavior beyond hook contracts.
- Full bilingual CLI surface beyond the current structured JSON and English error baseline.

## Continuation Queue
1. Introduce a real `codex_subscription` executor behind the existing role-policy contract, or keep it deferred if the non-interactive runtime path remains unstable.
2. Introduce live `review --auto` support for additional candidates once a safe reviewer runtime exists beyond `claude api`.
3. Introduce real diff ingestion and richer artifact metadata so review results can reference concrete code changes.
4. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
5. Add richer list filters and historical views for large local stores.
6. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review
- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path for both `local` and `real` presets, a first role ontology with local and real role-policy presets, provider-aware preflight checks, executor API runners with explicit `--access-mode api` selection, a Claude subscription executor runner, auto-generated `plan --auto` and `review --auto` flows, an explicit fallback approval request path, standalone preflight snapshots, and list-oriented CLI navigation for the main local records.
- The next session should preserve the current ontology and approval boundaries while improving real provider adapters, provenance, and richer read-side filtering instead of broadening scope.
