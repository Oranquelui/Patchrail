# Patchrail Backlog

## Next Milestones
1. Replace the current local-harness execution path with real `codex`, `claude`, and `grok` API and subscription adapters while keeping the current role-policy contract stable.
2. Promote isolated run workspaces from simple manifest folders into real execution sandboxes with stronger provenance.
3. Capture richer diffs, review summaries, and provenance metadata from runner outputs.
4. Add richer filters and history views on top of the current list surface so the local store stays usable as record volume grows.
5. Add finer-grained approval policies such as time-bounded fallback approvals and role-specific approvers.

## Deferred Features
- Dashboard or browser-based review UI.
- Generic provider marketplace behavior.
- Billing, quotas, or cloud tenancy concerns.
- Autonomous merges or approvals.
- Multi-user coordination or remote sync.
- Infra control center behavior beyond hook contracts.
- Full bilingual CLI surface beyond the current structured JSON and English error baseline.

## Continuation Queue
1. Introduce real provider adapters behind the existing role-policy contract, starting with `codex_api`, `claude_subscription`, and `grok_api`, and then close the remaining `codex_subscription`, `claude_api`, and `grok_subscription` execution gaps.
2. Introduce real diff ingestion and richer artifact metadata so review results can reference concrete code changes.
3. Add time-bounded or one-shot semantics for fallback approvals once real adapters exist.
4. Add richer list filters and historical views for large local stores.
5. Convert hook placeholders into event subscribers after approval and audit semantics are stable.

## Iteration Review
- This iteration establishes the durable contract, local storage layout, core state machine, CLI skeleton, isolated run workspaces, built-in local smoke-testing path, a first role ontology with local and real role-policy presets, provider-aware preflight checks, an explicit fallback approval request path, standalone preflight snapshots, and list-oriented CLI navigation for the main local records.
- The next session should preserve the current ontology and approval boundaries while improving real provider adapters, provenance, and richer read-side filtering instead of broadening scope.
