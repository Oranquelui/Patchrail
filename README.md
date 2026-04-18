# Patchrail

Patchrail は、ローカルファーストで supervised な coding-agent control plane です。現段階では CLI と headless core に絞り、`task -> plan -> run -> review -> approval` の状態遷移、artifact bundle、decision trace、approval ledger をローカルに残します。現在は `planner / reviewer / executor` に対して `provider × access_mode(api|subscription)` の候補集合を持ち、各フェーズ開始時に preflight と policy 解決を行って concrete assignment を固定保存します。

## Quickstart
```bash
cd /path/to/Patchrail
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
# optional workflow backend
pip install -e '.[langgraph]'
# deterministic local flow
python3 -m patchrail.cli config init
python3 -m patchrail.cli config init --workflow-backend langgraph
python3 -m patchrail.cli preflight --role planner
# live readiness checks
python3 -m patchrail.cli config init --preset real --workflow-backend local
python3 -m patchrail.cli preflight --role executor --runner auto
pytest -q
sh scripts/local_smoke_test.sh
PATCHRAIL_CONFIG_PRESET=real PATCHRAIL_AUTO_APPROVE_FALLBACK=1 sh scripts/local_smoke_test.sh
PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh
python3 -m patchrail.cli list tasks
python3 -m patchrail.cli list preflight-snapshots
python3 -m patchrail.cli list artifact-bundles --has-trace
```

`config init` は `.patchrail/config/role-policy.json` と `.patchrail/config/workflow-backend.json` を作成します。デフォルトの `local` preset は local harness を使う simulation-backed な subscription 候補を含むため、実 API や実 CLI login がなくてもローカルでフロー確認できます。`config init --preset real` は live-readiness 用の role policy を書き出し、subscription 候補の preflight を実 CLI で確認します。workflow backend は CLI-first に `config init --workflow-backend local|langgraph` で保存し、`PATCHRAIL_WORKFLOW_BACKEND` は一時 override としてだけ使います。

`real` preset の subscription preflight は現在こう動きます。
- `codex`: `codex login status`
- `claude`: `claude auth status`

`grok` は現在 API-only です。default policy には `grok subscription` 候補を入れていません。

`real` preset の API 候補は標準的な credential env を使います。
- `codex`: `OPENAI_API_KEY`
- `claude`: `ANTHROPIC_API_KEY`
- `grok`: `XAI_API_KEY`

`scripts/local_smoke_test.sh` は現在 `local` と `real` の両 preset を扱えます。
- `local`: `sh scripts/local_smoke_test.sh`
- `real`: `PATCHRAIL_CONFIG_PRESET=real PATCHRAIL_AUTO_APPROVE_FALLBACK=1 sh scripts/local_smoke_test.sh`
- `local auto plan/review`: `PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh`
- `langgraph auto plan/review`: `PATCHRAIL_WORKFLOW_BACKEND=langgraph PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh`

executor の API path を試す場合は `--access-mode api` を使います。たとえば Grok API executor は次で選べます。

```bash
python3 -m patchrail.cli preflight --role executor --runner grok_runner --access-mode api
python3 -m patchrail.cli run --task-id <task_id> --runner grok_runner --access-mode api
```

Claude subscription execution も live runner で試せます。

```bash
python3 -m patchrail.cli preflight --role executor --runner claude_code --access-mode subscription
python3 -m patchrail.cli run --task-id <task_id> --runner claude_code --access-mode subscription
```

planner / reviewer も auto path を持ちます。manual 入力を残したまま、`--auto` で role candidate に生成を任せられます。

```bash
python3 -m patchrail.cli config init --workflow-backend local
python3 -m patchrail.cli plan --task-id <task_id> --auto
python3 -m patchrail.cli review --run-id <run_id> --auto
python3 -m patchrail.cli review --run-id <run_id> --auto --access-mode api
```

LangGraph を使う場合は optional dependency を入れた上で backend を切り替えます。Patchrail に入るのは LangGraph runtime であり、LangGraph Studio は必須ではありません。Studio は graph 可視化・実行・デバッグ用の UI で、Patchrail の canonical control plane には入りません。

```bash
pip install -e '.[langgraph]'
python3 -m patchrail.cli config init --workflow-backend langgraph
python3 -m patchrail.cli plan --task-id <task_id> --auto
```

現在の LangGraph backend は planner / reviewer に対して stateless な 4-node graph を使います。
- planner: `collect_plan_context -> generate_plan -> validate_plan -> finalize_plan`
- reviewer: `collect_review_context -> generate_review -> validate_review -> finalize_review`

各 auto record には `workflow_metadata.node_trace`, `graph_version`, `checkpointer`, `delegate_backend` が補助情報として残ります。

artifact bundle には path map に加えて manifest-style metadata も残ります。各 artifact entry は `logical_kind`, `media_type`, `collection_status`, `sha256`, `size_bytes` を持ち、runner が structured trace を返した場合は `trace.json` として一緒に保存されます。`status --task-id ...` は `latest_artifact_bundle` まで返し、`list artifact-bundles [--task-id ...] [--logical-kind ...] [--has-trace]` で artifact history を read-side から辿れます。

現時点では、auto generation の live support は次です。
- planner: `claude subscription`, `codex api`
- reviewer: `claude api`
- executor: `claude subscription`, `codex api`, `claude api`, `grok api`

`codex subscription` は non-interactive runtime がまだ不安定なので、auto review / executor の live path では既定採用していません。

cross-provider または cross-access-mode の fallback が必要になった場合、Patchrail は fallback request を自動生成し、`patchrail approve-fallback --task-id ...` または `patchrail reject-fallback --task-id ...` で明示決定を要求します。

ローカルストアを直接開かなくても、`patchrail list tasks|plans|runs|reviews|approvals|fallback-requests|preflight-snapshots|artifact-bundles` で主要レコードを一覧できます。

## Docs
- [Architecture](docs/architecture.md)
- [MVP](docs/mvp.md)
- [Local Testing](docs/local-testing.md)
- [Backlog](docs/backlog.md)
- [Agents Contract](AGENTS.md)
