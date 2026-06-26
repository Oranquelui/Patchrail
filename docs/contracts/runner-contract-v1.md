# Runner Contract v1

Patchrail Runner Contract v1 defines the local handoff between Patchrail-owned canonical state and a supervised executor runner.

Schema version: `patchrail.runner_contract.v1`

Operator inspection:

```bash
patchrail contracts runner
patchrail --json contracts runner
```

The command is read-only. It reports the v1 workspace files, reserved environment variables, runner-writable paths, and forbidden ownership boundaries without creating tasks, runs, artifacts, or lifecycle transitions.

## Boundary

- Patchrail owns canonical task lifecycle state, plans, reviews, approvals, ledgers, and artifact bundles.
- Runners receive task and plan snapshots inside a per-run workspace.
- Runners may write execution output, runner-local artifacts, and runner trace data.
- Runners do not approve work, change task state, overwrite canonical plans, or own review verdicts.

## Workspace

Patchrail creates one workspace per run:

```text
.patchrail/workspaces/<run_id>/
```

Required v1 workspace files:

- `task.json`: serialized task snapshot.
- `plan.json`: serialized plan snapshot.
- `output.json`: runner output manifest written by shell runners when available.

Runner-writable v1 paths:

- `output.json`
- `artifacts/`
- `trace.json`

The `artifacts/` directory and `trace.json` path are reserved for runner-local exchange. Patchrail still creates the canonical evidence bundle under `.patchrail/artifacts/<run_id>/`.

After a runner exits, Patchrail collects regular files from `artifacts/`, copies them into `.patchrail/artifacts/<run_id>/runner-artifacts/`, and records each copied file in the Evidence Bundle v1 manifest with logical kind `runner_artifact`. The runner-owned exchange directory is therefore not the canonical artifact bundle.

## Reserved Environment Variables

Shell-backed runners receive these reserved variables:

- `PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION`
- `PATCHRAIL_RUN_ID`
- `PATCHRAIL_RUNNER_NAME`
- `PATCHRAIL_WORKSPACE`
- `PATCHRAIL_TASK_FILE`
- `PATCHRAIL_PLAN_FILE`
- `PATCHRAIL_OUTPUT_FILE`
- `PATCHRAIL_ARTIFACT_DIR`
- `PATCHRAIL_TRACE_FILE`

Existing shell runners may continue using only `PATCHRAIL_TASK_FILE`, `PATCHRAIL_PLAN_FILE`, and `PATCHRAIL_OUTPUT_FILE`. The additional variables are additive and reserved for v1-compatible runners.

## Output Manifest

When a shell runner writes `PATCHRAIL_OUTPUT_FILE`, Patchrail currently reads:

- `execution_summary`
- `diff_summary`
- `cost_metrics`
- `runner_trace`

`runner_trace` is optional. If present, Patchrail persists it as evidence under the canonical artifact bundle.

The built-in local harness includes runtime compatibility evidence inside `runner_trace.contract_runtime`:

- `reserved_environment_present`: the reserved v1 environment variables observed by the runner process.
- `workspace_relative_paths`: the task, plan, output, artifact, and trace paths relative to `PATCHRAIL_WORKSPACE`.
- `runner_writable_paths_ready`: the v1 runner-writable paths whose directory or parent directory was available during execution.
- `runner_contract_schema_version`: the contract schema version value observed from `PATCHRAIL_RUNNER_CONTRACT_SCHEMA_VERSION`.

The local harness also mirrors the structured trace to `PATCHRAIL_TRACE_FILE`. Patchrail still treats that file as runner-local exchange data and persists canonical evidence through the artifact bundle.

The local harness writes `local-harness-report.json` into `PATCHRAIL_ARTIFACT_DIR`. A successful smoke run should expose it in the canonical bundle as `runner_artifact:local-harness-report.json`.

## Forbidden Ownership

Runner Contract v1 explicitly excludes runner ownership of:

- `task_lifecycle_state`
- `canonical_plan`
- `review_verdict`
- `approval_decision`
- `approval_ledger`

Changing those ownership boundaries requires human approval before implementation.
