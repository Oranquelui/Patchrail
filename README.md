# Patchrail

Patchrail is a local-first supervised coding-agent control plane for future-anchored product execution. It stays focused on a CLI-first, headless-core-first workflow that records `task -> plan -> run -> review -> approval` as explicit local state transitions, together with artifact bundles, decision traces, and approval ledgers.

![Patchrail start screen](patchrail-start.jpg)

Patchrail keeps coding-agent supervision in a local CLI instead of hiding planning, review, approval, and artifacts behind a backend runtime.

Japanese usage notes live in [README.ja.md](README.ja.md).

## What You Can Show In 3 Minutes

Patchrail demonstrates a practical safety boundary for coding agents in customer or client repositories:

1. Create a task that describes the supervised work.
2. Attach future, ontology, and product briefs before implementation begins.
3. Store a canonical plan that references those briefs.
4. Run an executor behind an explicit runner assignment.
5. Review the persisted run artifacts before any final approval.
6. Record the human approval decision and ledgers locally.

The point is not to make an agent autonomous by default. The point is to make the handoff between human intent, agent execution, review evidence, and final approval inspectable from disk.

For a public-facing walkthrough, see [Supervised Agent Rollout](docs/case-studies/supervised-agent-rollout.md).

## Why Patchrail

- Keep the canonical workflow record in Patchrail rather than in a backend runtime.
- Preserve clear role separation across planner, reviewer, executor, and human approver.
- Constrain present implementation work with operator-defined completion, ontology, and scope documents rather than letting the next tool call decide the shape of the product.
- Make approval boundaries, fallback approvals, artifacts, and decision traces inspectable from disk.
- Support optional workflow backends, including LangGraph, without handing over canonical state ownership.

## Phase 1 Direction

The next planning layer is aimed at turning Patchrail into a supervised control plane for product definition before execution starts.

Phase 1 is structured around two onboarding passes:

- `machine/runtime onboarding`: select the provider set, access modes, and workflow backend that this machine can supervise safely
- `project/planning onboarding`: define the task, `Future Completion Brief`, `Ontology Brief`, `Product Brief`, and then generate the canonical plan

The brief sequence is intentionally ordered:

1. `Future Completion Brief` / prediction layer: describe what should be true in the future, the invariants that must hold, the failure conditions, and the non-goals.
2. `Ontology Brief` / reality-boundary layer: define what exists, what does not exist, who owns what, and where approval or artifact boundaries sit.
3. `Product Brief` / post-implementation acceptance layer: define the user problem, the MVP boundary, and what must be true after implementation for users and operators.
4. `Plan` / execution-translation layer: convert those constraints into executable implementation steps that Patchrail can supervise.
5. `Harness` / post-implementation evidence layer: after executor run and before review, capture execution summary, diff summary, stdout/stderr, invocation, runner trace, and artifact metadata.

Patchrail continues to own the canonical `Task`, `Plan`, `Run`, `ReviewResult`, `ApprovalRecord`, ledgers, and artifact bundles. The future, ontology, and product briefs are plan-scoped companion artifacts or metadata, not a second canonical state machine.

The first local path for that layer is available through:

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

From the repository root:

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

The `patchrail` command is exposed through the package entrypoint. `scripts/install_cli.sh` only installs that entrypoint via `pipx`. If your default `python3` is older than 3.12, pass an explicit interpreter path such as `--python /opt/homebrew/bin/python3.13`.

Patchrail defaults to human-readable CLI output. Use `patchrail --json ...` only for automation and scripting.

`patchrail setup` is the first-run CLI path. It bootstraps runtime config, runs role preflight checks, and returns concrete next commands. Use `patchrail setup project --title ... --description ...` to create a task plus editable planning brief scaffolds. Edit those files, persist them with `patchrail brief create ...`, and only then create the canonical plan.

## Quickstart

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail setup
patchrail setup project --title "First task" --description "Describe the supervised work"
# edit the generated future/ontology/product files, then persist each edited brief
patchrail brief create --task-id <task_id> --kind future --file <future_brief_file>
patchrail brief create --task-id <task_id> --kind ontology --file <ontology_brief_file>
patchrail brief create --task-id <task_id> --kind product --file <product_brief_file>
patchrail plan --task-id <task_id> --auto
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
patchrail list fallback-requests
patchrail list preflight-snapshots
patchrail list artifact-bundles --has-trace
patchrail --json status --task-id <task_id>
```

## Docs

- [Architecture](docs/architecture.md)
- [MVP](docs/mvp.md)
- [Local Testing](docs/local-testing.md)
- [Backlog](docs/backlog.md)
- [Changelog](CHANGELOG.md)
- [Agents Contract](AGENTS.md)
- [Japanese README](README.ja.md)

## License

MIT. See [LICENSE](LICENSE).
