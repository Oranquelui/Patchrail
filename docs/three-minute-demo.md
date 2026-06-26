# Patchrail 3-Minute Demo

## Demo Goal

Show that Patchrail is not another code-generation agent. It is a local verification and approval layer for AI-coded changes: it records what was planned, what ran, which verification command was executed, and what evidence is ready for human review.

## Talk Track

Opening, 20 seconds:

> AI coding agents can generate changes quickly, but senior developers still need evidence. Patchrail is a local-first CLI that turns an agent run into an auditable approval packet.

Core workflow, 90 seconds:

1. A task anchors the supervised work.
2. A Delivery Contract captures future state, ontology boundaries, and product acceptance before execution.
3. A run records the executor assignment, workspace, logs, and artifact bundle.
4. `patchrail verify` runs an operator-chosen command such as `pytest -q` and stores stdout, stderr, exit code, elapsed time, and status.
5. `patchrail packet show` produces the Markdown evidence a human reviewer can inspect.

Close, 30 seconds:

> The design choice is deliberate: Patchrail does not approve automatically, does not hide state in a dashboard, and does not flatten providers into a generic model wrapper. It gives a serious user a local record they can inspect, resume, and defend.

## Fast Local Demo

From a source checkout:

```bash
export PATCHRAIL_HOME="$(mktemp -d)"
sh scripts/local_smoke_test.sh
```

The smoke output prints a task id, run id, verification id, final state, and packet path. Use those ids for the follow-up inspection commands:

```bash
patchrail list verifications --task-id <task_id>
patchrail list review-queue
patchrail packet show --task-id <task_id>
```

Expected proof points:

- The verification record is `passed`.
- The review queue shows the completed task under `approved`.
- The approval packet contains task, plan, run, artifacts, verification, review, approval, and unresolved gaps.

## Manual Demo Variant

Use this when you want to show the public command surface rather than the smoke script:

```bash
patchrail setup
patchrail setup project --guided --title "Demo task" --description "Verify an AI-coded change"
patchrail plan --task-id <task_id> --summary "Run and verify agent output" --step "Execute supervised run" --step "Verify output"
patchrail run --task-id <task_id> --runner auto
patchrail verify --run-id <run_id> --command "pytest -q"
patchrail packet show --task-id <task_id>
```

If the demo environment does not have the full test suite available, replace `pytest -q` with a deterministic command:

```bash
patchrail verify --run-id <run_id> --command "python -c 'print(\"verification ok\")'"
```

## Interview Emphasis

- Product focus: the project pivoted from broad orchestration to a sharper verification need.
- State discipline: verification is intentionally stored as evidence without changing the canonical lifecycle yet.
- Local-first architecture: every record is readable under `.patchrail/`.
- Safety boundary: human approval remains explicit even when an agent and verification both succeed.
- Distribution readiness: package metadata, pipx-based local install docs, smoke tests, wheel checks, and release checks are part of the project.
