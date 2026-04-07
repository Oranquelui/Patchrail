# Patchrail

Patchrail は、ローカルファーストで supervised な coding-agent control plane です。現段階では CLI と headless core に絞り、`task -> plan -> run -> review -> approval` の状態遷移、artifact bundle、decision trace、approval ledger をローカルに残します。現在は `planner / reviewer / executor` に対して `provider × access_mode(api|subscription)` の候補集合を持ち、各フェーズ開始時に preflight と policy 解決を行って concrete assignment を固定保存します。

## Quickstart
```bash
cd /path/to/Patchrail
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
# deterministic local flow
python3 -m patchrail.cli config init
python3 -m patchrail.cli preflight --role planner
# live readiness checks
python3 -m patchrail.cli config init --preset real
python3 -m patchrail.cli preflight --role executor --runner auto
pytest -q
sh scripts/local_smoke_test.sh
PATCHRAIL_CONFIG_PRESET=real PATCHRAIL_AUTO_APPROVE_FALLBACK=1 sh scripts/local_smoke_test.sh
python3 -m patchrail.cli list tasks
python3 -m patchrail.cli list preflight-snapshots
```

`config init` は `.patchrail/config/role-policy.json` を作成します。デフォルトの `local` preset は local harness を使う simulation-backed な subscription 候補を含むため、実 API や実 CLI login がなくてもローカルでフロー確認できます。`config init --preset real` は live-readiness 用の role policy を書き出し、subscription 候補の preflight を実 CLI で確認します。

`real` preset の subscription preflight は現在こう動きます。
- `codex`: `codex login status`
- `claude`: `claude auth status`
- `grok`: 現行統合では non-interactive status が安定していないため blocked 扱い

`real` preset の API 候補は標準的な credential env を使います。
- `codex`: `OPENAI_API_KEY`
- `claude`: `ANTHROPIC_API_KEY`
- `grok`: `XAI_API_KEY`

`scripts/local_smoke_test.sh` は現在 `local` と `real` の両 preset を扱えます。
- `local`: `sh scripts/local_smoke_test.sh`
- `real`: `PATCHRAIL_CONFIG_PRESET=real PATCHRAIL_AUTO_APPROVE_FALLBACK=1 sh scripts/local_smoke_test.sh`

executor の API path を試す場合は `--access-mode api` を使います。たとえば Grok API executor は次で選べます。

```bash
python3 -m patchrail.cli preflight --role executor --runner grok_runner --access-mode api
python3 -m patchrail.cli run --task-id <task_id> --runner grok_runner --access-mode api
```

cross-provider または cross-access-mode の fallback が必要になった場合、Patchrail は fallback request を自動生成し、`patchrail approve-fallback --task-id ...` または `patchrail reject-fallback --task-id ...` で明示決定を要求します。

ローカルストアを直接開かなくても、`patchrail list tasks|plans|runs|reviews|approvals|fallback-requests|preflight-snapshots` で主要レコードを一覧できます。

## Docs
- [Architecture](docs/architecture.md)
- [MVP](docs/mvp.md)
- [Local Testing](docs/local-testing.md)
- [Backlog](docs/backlog.md)
- [Agents Contract](AGENTS.md)
