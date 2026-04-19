# Local Testing

## Goal
Patchrail を手元で end-to-end に試し、task 生成から approval までの最小フローとローカル永続化を確認する。

## Install CLI
```bash
cd /path/to/Patchrail
brew install pipx
pipx ensurepath
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail --help
```

optional LangGraph runtime まで同じ install 導線で入れる場合:
```bash
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
```

## Fastest Path
1. CLI を install する。
```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)"
```
2. role policy を初期化し、preflight を確認する。
```bash
# local preset
patchrail config init
patchrail config init --workflow-backend langgraph
patchrail preflight --role planner
patchrail preflight --role reviewer
patchrail preflight --role executor --runner auto

# real preset
patchrail config init --preset real --workflow-backend local
patchrail preflight --role executor --runner auto

# api executor path
patchrail preflight --role executor --runner grok_runner --access-mode api
```
3. テストを実行する。
```bash
pytest -q
```
4. smoke flow を実行する。
```bash
sh scripts/local_smoke_test.sh
PATCHRAIL_CONFIG_PRESET=real PATCHRAIL_AUTO_APPROVE_FALLBACK=1 sh scripts/local_smoke_test.sh
PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh
PATCHRAIL_WORKFLOW_BACKEND=langgraph PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh
```
5. 保存済みレコードを一覧する。
```bash
patchrail list tasks
patchrail list plans
patchrail list runs
patchrail list reviews
patchrail list approvals
patchrail list fallback-requests
patchrail list preflight-snapshots
patchrail list artifact-bundles --has-trace
```

`scripts/local_smoke_test.sh` は以下を自動で行う:
- `config init`
- `preflight`
- `task create`
- `plan`
- `run --runner auto`
- `review`
- `approve`

利用可能な環境変数:
- `PATCHRAIL_CONFIG_PRESET=local|real`
- `PATCHRAIL_WORKFLOW_BACKEND=local|langgraph`
- `PATCHRAIL_RUNNER=auto|claude_code|grok_runner|codex_runner`
- `PATCHRAIL_AUTO_APPROVE_FALLBACK=0|1`
- `PATCHRAIL_AUTO_PLAN=0|1`
- `PATCHRAIL_PLAN_ACCESS_MODE=auto|api|subscription`
- `PATCHRAIL_AUTO_REVIEW=0|1`
- `PATCHRAIL_REVIEW_ACCESS_MODE=auto|api|subscription`

デフォルトの `local` preset は `planner / reviewer / executor` に simulation-backed な subscription 候補を持ち、`python -m patchrail.runners.local_harness` を command として使う。これにより、実際の API key や CLI login がなくても policy 解決と end-to-end flow を再現できる。workflow backend は `config init --workflow-backend local|langgraph` で永続化され、`PATCHRAIL_WORKFLOW_BACKEND` は smoke や一時検証向けの override として使える。

`real` preset を使う場合:
- `python3 -m patchrail.cli config init --preset real`
- `codex subscription` は `codex login status` を使う
- `claude subscription` は `claude auth status` を使う
- `grok` は API-only で、`grok subscription` 候補は既定 policy に含めない

API 候補を試す場合は、対応する環境変数を設定する:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `XAI_API_KEY`

API executor の最短手順:
```bash
python3 -m patchrail.cli preflight --role executor --runner grok_runner --access-mode api
python3 -m patchrail.cli run --task-id <task_id> --runner grok_runner --access-mode api
```

Claude subscription executor の最短手順:
```bash
python3 -m patchrail.cli preflight --role executor --runner claude_code --access-mode subscription
python3 -m patchrail.cli run --task-id <task_id> --runner claude_code --access-mode subscription
```

Codex subscription executor の最短手順:
```bash
python3 -m patchrail.cli preflight --role executor --runner codex_runner --access-mode subscription
python3 -m patchrail.cli run --task-id <task_id> --runner codex_runner --access-mode subscription
```

Auto planner / reviewer の最短手順:
```bash
python3 -m patchrail.cli config init --workflow-backend local
python3 -m patchrail.cli plan --task-id <task_id> --auto
python3 -m patchrail.cli review --run-id <run_id> --auto

# real preset で reviewer を Codex subscription path に寄せる場合
python3 -m patchrail.cli review --run-id <run_id> --auto

# real preset で reviewer を Claude API path に寄せる場合
python3 -m patchrail.cli review --run-id <run_id> --auto --access-mode api
```

LangGraph backend を試す最短手順:
```bash
pip install -e '.[langgraph]'
python3 -m patchrail.cli config init --workflow-backend langgraph
python3 -m patchrail.cli plan --task-id <task_id> --auto
```

成功すると、plan / review JSON に `workflow_backend=langgraph` と `workflow_metadata.node_trace` が残る。現行 MVP の graph は stateless なので、LangGraph の subordinate state は canonical continuation data にはせず、Patchrail record に要約 metadata だけを保存する。

artifact metadata を確認する最短手順:
```bash
python3 -m patchrail.cli status --task-id <task_id>
python3 -m patchrail.cli list artifact-bundles --task-id <task_id>
python3 -m patchrail.cli list artifact-bundles --logical-kind runner_trace --has-trace
```

## Manual Flow
```bash
cd /path/to/Patchrail
export PATCHRAIL_HOME="$PWD/.patchrail"

# local preset
python3 -m patchrail.cli config init
python3 -m patchrail.cli preflight --role planner
python3 -m patchrail.cli preflight --role reviewer
python3 -m patchrail.cli preflight --role executor --runner auto

# real preset
python3 -m patchrail.cli config init --preset real
python3 -m patchrail.cli preflight --role executor --runner auto
python3 -m patchrail.cli preflight --role executor --runner grok_runner --access-mode api

python3 -m patchrail.cli task create \
  --title "Manual local test" \
  --description "Verify local flow"

python3 -m patchrail.cli plan \
  --task-id <task_id> \
  --summary "Run local harness" \
  --step "Resolve planner candidate" \
  --step "Run harness"

python3 -m patchrail.cli run --task-id <task_id> --runner auto
python3 -m patchrail.cli review --run-id <run_id> --verdict pass --summary "Looks good"
python3 -m patchrail.cli approve --task-id <task_id> --rationale "Local test passed"
python3 -m patchrail.cli status --task-id <task_id>
python3 -m patchrail.cli artifacts --run-id <run_id>
python3 -m patchrail.cli logs --run-id <run_id>
python3 -m patchrail.cli list artifact-bundles --task-id <task_id>
python3 -m patchrail.cli list tasks
python3 -m patchrail.cli list plans --task-id <task_id>
python3 -m patchrail.cli list runs --task-id <task_id>
python3 -m patchrail.cli list reviews --task-id <task_id>
python3 -m patchrail.cli list approvals --task-id <task_id>
python3 -m patchrail.cli list preflight-snapshots --task-id <task_id>
```

cross-provider または cross-access-mode fallback を試す場合:
```bash
python3 -m patchrail.cli run --task-id <task_id> --runner auto
python3 -m patchrail.cli status --task-id <task_id>
python3 -m patchrail.cli approve-fallback --task-id <task_id> --rationale "Allow deviation"
python3 -m patchrail.cli run --task-id <task_id> --runner auto
```

`real` preset では executor の先頭候補が `grok api` だが、`XAI_API_KEY` が無い場合は `claude subscription` への fallback approval が必要になる。これは監査境界を確認するための意図的な構成。

一方で `--runner grok_runner --access-mode api` を使えば、`grok_api_executor` を直接選べる。これは live API path の疎通確認に向いている。

`--runner claude_code --access-mode subscription` を使えば、`claude_subscription_executor` を直接選べる。これは live subscription path の疎通確認に向いている。

`--runner codex_runner --access-mode subscription` を使えば、`codex_subscription_executor` を直接選べる。workspace 非 git directory でも `codex exec --skip-git-repo-check` 経由で supervised execution を試せる。

最短の real smoke:
```bash
PATCHRAIL_HOME="$PWD/.patchrail-real" \
PATCHRAIL_CONFIG_PRESET=real \
PATCHRAIL_AUTO_APPROVE_FALLBACK=1 \
sh scripts/local_smoke_test.sh
```

最短の local auto smoke:
```bash
PATCHRAIL_HOME="$PWD/.patchrail-auto" \
PATCHRAIL_AUTO_PLAN=1 \
PATCHRAIL_AUTO_REVIEW=1 \
sh scripts/local_smoke_test.sh
```

## Files To Inspect
- `.patchrail/tasks/`
- `.patchrail/plans/`
- `.patchrail/runs/`
- `.patchrail/reviews/`
- `.patchrail/approvals/`
- `.patchrail/fallback_requests/`
- `.patchrail/preflight_snapshots/`
- `.patchrail/config/role-policy.json`
- `.patchrail/config/workflow-backend.json`
- `.patchrail/artifacts/<run_id>/`
- `.patchrail/artifacts/<run_id>/trace.json`
- `.patchrail/workspaces/<run_id>/`
- `.patchrail/ledgers/`
