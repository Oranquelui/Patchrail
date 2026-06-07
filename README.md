# Patchrail

Patchrail is a local-first verification and approval packet CLI for AI coding agent work. Run Claude, Codex, Cursor, or another coding workflow, then use Patchrail to prove what changed, what was verified, and whether the result is ready for human approval.

![Patchrail terminal loading screen](patchrail-start.jpg)

Terminal loading/start screen rendered by `patchrail start`. Patchrail is intentionally usable from a terminal before any hosted dashboard exists.

Patchrail keeps coding-agent supervision in a local CLI instead of hiding plans, runs, verification output, review decisions, approval ledgers, and artifacts behind a backend runtime.

Japanese usage notes live in [README.ja.md](README.ja.md).

## What This Demonstrates

Patchrail is intended to be read as a serious engineering portfolio project, not only as a CLI prototype. It demonstrates:

- Product judgment: narrowing the problem from generic agent orchestration to verification and approval packets for AI-coded changes.
- Systems design: explicit lifecycle records, role separation, approval boundaries, local persistence, and resumable state.
- Practical CLI execution: commands that create tasks, capture Delivery Contracts, run executors, record verification, and export review-ready packets.
- Engineering discipline: focused tests, smoke tests, package metadata, release checks, and a local-first storage model that can be inspected from disk.

For interview-oriented material, see the [3-minute demo guide](docs/three-minute-demo.md) and [resume positioning notes](docs/resume-positioning.md).

## Development Purpose

Patchrail is being developed to make AI-coded changes auditable before, during, and after implementation. Modern coding agents can move from a vague instruction to repository changes very quickly; the hard part is proving what the operator meant, what changed, which checks ran, and why a human approved or rejected the result.

The core purpose is to preserve that chain as local, inspectable records:

```text
human intent -> delivery contract -> plan snapshot -> runner execution -> verification evidence -> review -> approval packet
```

This is why Patchrail starts with a CLI and headless core rather than a dashboard. The first requirement is not presentation. The first requirement is a reliable local record that can be checked, diffed, tested, packaged, and reviewed without trusting a remote service.

## Why This Is Necessary

Coding-agent workflows usually fail in the gaps between intention, execution, and review:

- A chat transcript can describe intent, but it is not a durable operational record.
- A plan can look reasonable, but it becomes unsafe if it is disconnected from the assumptions and boundaries that produced it.
- A review can inspect the final diff, but it cannot reconstruct whether the executor stayed inside the original product, ontology, and approval boundaries.
- A dashboard can make the workflow look organized, but it can also hide which system owns canonical state, evidence, and final approval.

Patchrail addresses those gaps by separating five concerns:

1. Predict the desired future state before implementation.
2. Define the real-world ontology and approval boundaries before implementation.
3. Define post-implementation acceptance criteria before implementation.
4. Snapshot those inputs into a canonical plan before the runner executes.
5. Capture post-implementation evidence before review and approval.

The result is not an autonomous-agent launcher. It is a supervision rail: a local control plane that makes the handoff between human judgment and agent execution explicit.

## What You Can Show In 3 Minutes

Patchrail demonstrates a practical safety boundary for AI coding work:

1. Run an AI coding workflow behind an explicit Patchrail task and plan.
2. Record the executor run and artifact bundle in local storage.
3. Run `patchrail verify --run-id <run_id> --command "pytest -q"` to capture verification evidence.
4. Use `patchrail list review-queue` to separate missing verification, failed verification, ready-for-review, awaiting-approval, and approved tasks.
5. Export `patchrail packet show --task-id <task_id>` as the review-ready artifact.

The point is not to make an agent autonomous by default. The point is to make the handoff between human intent, agent execution, review evidence, and final approval inspectable from disk.

For a public-facing walkthrough, see the [3-minute demo guide](docs/three-minute-demo.md) and [Supervised Agent Rollout](docs/case-studies/supervised-agent-rollout.md).

## Why Patchrail

- Keep the canonical workflow record in Patchrail rather than in a backend runtime.
- Preserve clear role separation across planner, reviewer, executor, and human approver.
- Constrain present implementation work with operator-defined completion, ontology, and scope documents rather than letting the next tool call decide the shape of the product.
- Make approval boundaries, fallback approvals, artifacts, verification results, packets, and decision traces inspectable from disk.
- Support optional workflow backends, including LangGraph, without handing over canonical state ownership.

## v0.2 Direction

The next public release focuses on AI coding verification, not generic agent orchestration. The flagship loop is:

```bash
patchrail run --task-id <task_id> --runner auto
patchrail verify --run-id <run_id> --command "pytest -q"
patchrail list review-queue
patchrail packet show --task-id <task_id>
```

Verification records store the command, working directory, exit code, elapsed time, stdout path, and stderr path under `.patchrail/`. Approval packets gather the task, Delivery Contract, plan, run, runner assignment, artifact bundle, verification results, review verdict, approval decision, and unresolved gaps into Markdown or JSON.

The planning layer remains structured around two onboarding passes:

- `machine/runtime onboarding`: select the provider set, access modes, and workflow backend that this machine can supervise safely
- `project/planning onboarding`: define the task, Delivery Contract prompts, `Future Completion Brief`, `Ontology Brief`, `Product Brief`, and then generate the canonical plan

The public concept is the Delivery Contract. The stored compatibility model is still called `brief`, and the sequence is intentionally ordered:

1. `Future Completion Brief` / prediction layer: describe what should be true in the future, the invariants that must hold, the failure conditions, and the non-goals.
2. `Ontology Brief` / reality-boundary layer: define what exists, what does not exist, who owns what, and where approval or artifact boundaries sit.
3. `Product Brief` / post-implementation acceptance layer: define the user problem, the MVP boundary, and what must be true after implementation for users and operators.
4. `Plan` / execution-translation layer: convert those constraints into executable implementation steps that Patchrail can supervise.
5. `Verification` / post-implementation evidence layer: after executor run and before review, capture command results, stdout/stderr paths, exit codes, elapsed time, runner trace, and artifact metadata.

Patchrail continues to own the canonical `Task`, `Plan`, `Run`, `ReviewResult`, `ApprovalRecord`, ledgers, and artifact bundles. The future, ontology, and product briefs are plan-scoped companion artifacts or metadata, not a second canonical state machine.

The first local path for that contract layer is available through:

```bash
patchrail brief create --task-id <task_id> --kind future --file future.md
patchrail brief create --task-id <task_id> --kind ontology --file ontology.md
patchrail brief create --task-id <task_id> --kind product --file product.md
patchrail brief list --task-id <task_id>
patchrail brief show --brief-id <brief_id>
```

When `patchrail plan` stores the canonical plan, it snapshots references to the task's current briefs under `planning_briefs` while leaving the canonical state machine unchanged.

Phase 1 also gives the three live providers distinct planning roles instead of treating them as interchangeable model slots:

- `Codex / OpenAI`: structure the plan and preserve the supervisory viewpoint
- `Claude`: expand the implementation path and keep the plan coherent across longer reasoning spans
- `Grok`: challenge weak assumptions, missing constraints, and product drift

The goal is triangulated planning with explicit traces, not generic multi-model fan-out.

## Install CLI

Public install:

```bash
brew install pipx
pipx ensurepath
pipx install patchrail
patchrail --help
```

From a source checkout:

```bash
cd /path/to/Patchrail
brew install pipx
pipx ensurepath
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail --help
patchrail setup
patchrail start
```

To install the optional LangGraph runtime into the same `pipx` environment:

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
```

The `patchrail` command is exposed through the package entrypoint. Public users can install it with `pipx install patchrail`; source checkout users can run `scripts/install_cli.sh` for an editable install. If your default `python3` is older than 3.12, pass an explicit interpreter path such as `--python /opt/homebrew/bin/python3.13`.

Patchrail defaults to human-readable CLI output. Use `patchrail --json ...` only for automation and scripting.

`patchrail setup` is the first-run CLI path. It bootstraps runtime config, runs role preflight checks, and returns concrete next commands. Use `patchrail setup project --guided --title ... --description ...` to create a task plus editable Delivery Contract scaffolds. Edit those files, persist them with `patchrail brief create ...`, and only then create the canonical plan.

## Quickstart

```bash
cd /path/to/Patchrail
pipx install patchrail
patchrail setup
patchrail setup project --guided --title "First task" --description "Describe the supervised work"
# edit the generated future/ontology/product files, then persist each edited brief
patchrail brief create --task-id <task_id> --kind future --file <future_brief_file>
patchrail brief create --task-id <task_id> --kind ontology --file <ontology_brief_file>
patchrail brief create --task-id <task_id> --kind product --file <product_brief_file>
patchrail plan --task-id <task_id> --auto
patchrail run --task-id <task_id> --runner auto
patchrail verify --run-id <run_id> --command "pytest -q"
patchrail packet show --task-id <task_id>
```

`patchrail start` opens the interactive shell in TTY sessions. Use `patchrail start --once` to render the home screen and exit immediately.

Inside the shell you can run the existing subcommands directly:

```text
help
doctor
list tasks
task create --title "First task" --description "Describe the work"
exit
```

## Basic Flow

Deterministic local flow:

```bash
cd /path/to/Patchrail
patchrail setup
patchrail preflight --role planner
patchrail preflight --role reviewer
patchrail preflight --role executor --runner auto
sh scripts/local_smoke_test.sh
```

LangGraph-backed auto plan and review:

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
patchrail config init --workflow-backend langgraph
PATCHRAIL_WORKFLOW_BACKEND=langgraph PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh
```

Real readiness checks:

```bash
cd /path/to/Patchrail
patchrail config init --preset real --workflow-backend local
patchrail preflight --role executor --runner auto
```

## Workflow Backends

Patchrail keeps the canonical records for:

- `Task`
- `Plan`
- `Run`
- `ReviewResult`
- `ApprovalRecord`
- `Approval Ledger`
- `Decision Trace`
- `Artifact Bundle`

The default workflow backend is `local`. LangGraph is available as an optional subordinate backend for `plan --auto` and `review --auto`.

Current LangGraph graphs are stateless:

- planner: `collect_plan_context -> generate_plan -> validate_plan -> finalize_plan`
- reviewer: `collect_review_context -> generate_review -> validate_review -> finalize_review`

Patchrail stores only workflow metadata such as `graph_version`, `checkpointer`, `delegate_backend`, and `node_trace` on the canonical plan or review record. Approval meaning, artifact ownership, and the canonical state machine remain Patchrail-owned.

## Current Live Support

Auto generation:

- planner: `claude subscription`, `codex api`
- reviewer: `codex subscription`, `claude api`

Execution:

- `codex subscription`
- `claude subscription`
- `codex api`
- `claude api`
- `grok api`

`grok` is API-only in the default policy set. Patchrail does not currently ship a default `grok subscription` candidate.

## Local Storage

Patchrail persists state under `.patchrail/` or the directory pointed to by `PATCHRAIL_HOME`.

Useful read-side commands:

```bash
patchrail list tasks
patchrail brief list --task-id <task_id>
patchrail brief show --brief-id <brief_id>
patchrail list plans
patchrail list runs
patchrail list reviews
patchrail list approvals
patchrail list verifications --task-id <task_id>
patchrail list review-queue
patchrail list fallback-requests
patchrail list preflight-snapshots
patchrail list artifact-bundles --has-trace
patchrail --json status --task-id <task_id>
```

## Docs

- [Architecture](docs/architecture.md)
- [MVP](docs/mvp.md)
- [3-Minute Demo](docs/three-minute-demo.md)
- [Resume Positioning](docs/resume-positioning.md)
- [Local Testing](docs/local-testing.md)
- [Backlog](docs/backlog.md)
- [Changelog](CHANGELOG.md)
- [Agents Contract](AGENTS.md)
- [Japanese README](README.ja.md)

## License

MIT. See [LICENSE](LICENSE).
