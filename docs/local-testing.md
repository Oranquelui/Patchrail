# Local Testing

## Goal
Patchrail を手元で end-to-end に試し、task 生成から approval までの最小フローとローカル永続化を確認する。

## Fastest Path
1. 仮想環境を作る。
```bash
cd /path/to/Patchrail
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```
2. role policy を初期化し、preflight を確認する。
```bash
# local preset
python3 -m patchrail.cli config init
python3 -m patchrail.cli preflight --role planner
python3 -m patchrail.cli preflight --role reviewer
python3 -m patchrail.cli preflight --role executor --runner auto

# real preset
python3 -m patchrail.cli config init --preset real
python3 -m patchrail.cli preflight --role executor --runner auto

# api executor path
python3 -m patchrail.cli preflight --role executor --runner grok_runner --access-mode api
```
3. テストを実行する。
```bash
pytest -q
```
4. smoke flow を実行する。
```bash
sh scripts/local_smoke_test.sh
PATCHRAIL_CONFIG_PRESET=real PATCHRAIL_AUTO_APPROVE_FALLBACK=1 sh scripts/local_smoke_test.sh
```
5. 保存済みレコードを一覧する。
```bash
python3 -m patchrail.cli list tasks
python3 -m patchrail.cli list plans
python3 -m patchrail.cli list runs
python3 -m patchrail.cli list reviews
python3 -m patchrail.cli list approvals
python3 -m patchrail.cli list fallback-requests
python3 -m patchrail.cli list preflight-snapshots
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
- `PATCHRAIL_RUNNER=auto|claude_code|grok_runner|codex_runner`
- `PATCHRAIL_AUTO_APPROVE_FALLBACK=0|1`

デフォルトの `local` preset は `planner / reviewer / executor` に simulation-backed な subscription 候補を持ち、`python -m patchrail.runners.local_harness` を command として使う。これにより、実際の API key や CLI login がなくても policy 解決と end-to-end flow を再現できる。

`real` preset を使う場合:
- `python3 -m patchrail.cli config init --preset real`
- `codex subscription` は `codex login status` を使う
- `claude subscription` は `claude auth status` を使う
- `grok subscription` は現行統合では blocked 扱いになる

API 候補を試す場合は、対応する環境変数を設定する:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `XAI_API_KEY`

API executor の最短手順:
```bash
python3 -m patchrail.cli preflight --role executor --runner grok_runner --access-mode api
python3 -m patchrail.cli run --task-id <task_id> --runner grok_runner --access-mode api
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

`real` preset では executor の先頭候補が `grok subscription` のため、通常は `claude subscription` への fallback approval が必要になる。これは監査境界を確認するための意図的な構成。

一方で `--runner grok_runner --access-mode api` を使えば、`grok_api_executor` を直接選べる。これは live API path の疎通確認に向いている。

最短の real smoke:
```bash
PATCHRAIL_HOME="$PWD/.patchrail-real" \
PATCHRAIL_CONFIG_PRESET=real \
PATCHRAIL_AUTO_APPROVE_FALLBACK=1 \
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
- `.patchrail/artifacts/<run_id>/`
- `.patchrail/workspaces/<run_id>/`
- `.patchrail/ledgers/`
