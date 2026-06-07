# Local Testing

Patchrail is tested as a local-first CLI. Use a temporary `PATCHRAIL_HOME` when you want a clean run without touching the repo-local `.patchrail/` store.

## Install

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)"
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
```

Default output is human-readable. Use `patchrail --json ...` for machine-readable automation.

`patchrail setup` bootstraps runtime config and preflight summary. `patchrail setup project --guided --title ... --description ...` creates a task and Delivery Contract-oriented `future / ontology / product` brief scaffolds. Generated scaffolds and persisted brief records use `patchrail.brief_schema.v1`.

## Fastest Path

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail setup
patchrail setup project --guided --title "First task" --description "Describe the supervised work"
patchrail brief validate --task-id <task_id>
patchrail start
```

## Smoke Test

```bash
PATCHRAIL_HOME="$(mktemp -d)/.patchrail" \
PYTHON_BIN=/opt/homebrew/bin/python3.13 \
PATCHRAIL_CONFIG_PRESET=local \
PATCHRAIL_WORKFLOW_BACKEND=local \
sh scripts/local_smoke_test.sh
```

`scripts/local_smoke_test.sh` performs:

- `config init`
- planner, reviewer, and executor `preflight`
- `setup project --guided`
- `brief create` for `future`, `ontology`, and `product`
- `brief validate`
- `plan`
- `run --runner auto`
- `verify --command "$PATCHRAIL_VERIFY_COMMAND"`
- `review`
- `approve`
- `packet export`
- `packet show`

Expected final output includes:

```text
Local smoke flow completed: ...
Brief schema validation: schema=patchrail.brief_schema.v1 briefs=3
PATCHRAIL_HOME=...
```

## Useful Commands

```bash
patchrail config init --workflow-backend local
patchrail config init --workflow-backend langgraph
patchrail config init --preset real --workflow-backend local

patchrail preflight --role planner
patchrail preflight --role reviewer
patchrail preflight --role executor --runner auto
patchrail contracts runner

patchrail brief validate --task-id <task_id>
patchrail --json contracts runner
patchrail --json status --task-id <task_id>
patchrail verify --run-id <run_id> --command "pytest -q"
patchrail list verifications --run-id <run_id>
patchrail list review-queue
patchrail packet show --task-id <task_id>
patchrail packet export --task-id <task_id> --output approval-packet.md
```

## Artifact Checks

JSON output for `status`, `artifacts`, and `list artifact-bundles` includes `schema_version=patchrail.evidence_bundle.v1` on persisted evidence bundles.

The local harness trace includes `contract_runtime`, which records the observed Runner Contract v1 schema-version environment variable, workspace-relative handoff paths, and ready runner-writable paths. The same trace is mirrored to `.patchrail/workspaces/<run_id>/trace.json` before Patchrail persists it into the canonical evidence bundle.

Runner-local artifacts written under `.patchrail/workspaces/<run_id>/artifacts/` are copied into `.patchrail/artifacts/<run_id>/runner-artifacts/` and exposed as `runner_artifact` manifest entries. The local harness smoke path writes `local-harness-report.json` so operators can verify the collection path without external runner dependencies.

Verification stdout/stderr are stored under `.patchrail/verification_outputs/<verification_id>/`.

## Full Verification

```bash
/opt/homebrew/bin/python3.13 -m pytest -q
/opt/homebrew/bin/python3.13 -m compileall -q patchrail tests
/opt/homebrew/bin/python3.13 -m patchrail.cli --help
/opt/homebrew/bin/python3.13 -m patchrail.cli --json contracts runner
sh scripts/local_smoke_test.sh
```

Release package checks:

```bash
sh scripts/check_release.sh --python /opt/homebrew/bin/python3.13 --dry-run
sh scripts/check_release.sh --python /opt/homebrew/bin/python3.13
```

## Files Created

- `.patchrail/config/role-policy.json`
- `.patchrail/config/workflow-backend.json`
- `.patchrail/tasks/<task_id>.json`
- `.patchrail/briefs/<brief_id>.json`
- `.patchrail/plans/<plan_id>.json`
- `.patchrail/runs/<run_id>.json`
- `.patchrail/verifications/<verification_id>.json`
- `.patchrail/verification_outputs/<verification_id>/stdout.log`
- `.patchrail/verification_outputs/<verification_id>/stderr.log`
- `.patchrail/artifacts/<run_id>/`
- `.patchrail/artifacts/<run_id>/runner-artifacts/`
- `.patchrail/artifacts/<run_id>/trace.json`
- `.patchrail/workspaces/<run_id>/`
- `.patchrail/workspaces/<run_id>/task.json`
- `.patchrail/workspaces/<run_id>/plan.json`
- `.patchrail/workspaces/<run_id>/output.json`
- `.patchrail/workspaces/<run_id>/artifacts/`
- `.patchrail/workspaces/<run_id>/trace.json`
- `.patchrail/ledgers/`
