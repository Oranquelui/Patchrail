# Patchrail

Patchrail は、ローカルファーストで supervised な coding-agent control plane です。現段階では CLI と headless core に絞り、`task -> plan -> run -> review -> approval` の状態遷移、artifact bundle、decision trace、approval ledger をローカルに残します。現在は `planner / reviewer / executor` に対して `provider × access_mode(api|subscription)` の候補集合を持ち、各フェーズ開始時に preflight と policy 解決を行って concrete assignment を固定保存します。

![Patchrail terminal loading screen](patchrail-start.jpg)

`patchrail start` が描画する Terminal の loading/start 画面です。Patchrail は、hosted dashboard より前に、まず Terminal だけで監督・検証・承認の流れを扱えることを重視しています。

英語版の公開 README は [README.md](README.md) にあります。

## 開発趣旨

Patchrail は、coding agent を「速く動かす」ためだけの launcher ではありません。開発目的は、人間の意図、実装前の前提、agent の実行、実装後の証跡、レビュー、最終承認を、あとから検証できるローカル記録としてつなぐことです。

中心にある chain は次です。

```text
human intent -> planning briefs -> plan snapshot -> runner execution -> harness evidence -> review -> approval
```

coding agent は、曖昧な指示からでも短時間で repository を変更できます。しかし、業務や顧客環境では「何を正しい完了状態とみなしたのか」「どの境界を越えてはいけなかったのか」「実際に runner が何をしたのか」「なぜ人間が承認したのか」が残っていなければ、安全に導入できません。

そのため Patchrail は dashboard-first ではなく、CLI-first / headless-core-first で作っています。最初に必要なのは見た目ではなく、diff でき、test でき、review でき、ローカルに残る canonical record です。

## なぜ必要か

一般的な coding-agent workflow は、意図・実行・レビューの間にある隙間で壊れます。

- chat transcript は意図を説明できますが、運用上の durable record ではありません。
- plan は一見もっともらしく見えても、元の前提や境界から切り離されると危険です。
- final diff の review だけでは、executor が最初の product / ontology / approval boundary の内側に留まったかを復元できません。
- dashboard は整理されているように見えますが、canonical state、証跡、最終承認を誰が所有しているかを曖昧にすることがあります。

Patchrail はこの問題を、5つの責務に分けて扱います。

1. 実装前に、未来に成立しているべき状態を予測する。
2. 実装前に、現実の ontology と承認境界を定義する。
3. 実装前に、実装後の acceptance criteria を定義する。
4. runner 実行前に、それらを canonical plan へ snapshot する。
5. review / approval 前に、実装後の証跡を harness / artifact bundle として捕獲する。

つまり Patchrail は autonomous agent を無制限に走らせる道具ではなく、人間の判断と agent 実行の受け渡しを明示する supervision rail です。

## 3分で見せるポイント

Patchrail は、顧客・クライアントのリポジトリに AI coding agent を導入する際の安全境界を示すためのローカルファーストな control plane です。

1. 監督対象の task を作る。
2. 実装前に future / ontology / product brief を添付する。
3. それらの brief を参照する canonical plan を保存する。
4. 明示的な runner assignment のもとで executor を実行する。
5. final approval の前に run artifacts をレビューする。
6. human approval decision と ledger をローカルに残す。

目的は agent を最初から自律実行させることではありません。人間の意図、agent実行、レビュー証跡、最終承認の受け渡しを、あとからディスク上で確認できるようにすることです。

Layer構造は次の意味に固定しています。

| Layer | 対応物 | タイミング | 目的 |
| --- | --- | --- | --- |
| Prediction | Future Completion Brief | 実装前 | 未来に何が成立しているべきかを予測する。 |
| Reality boundary | Ontology Brief | 実装前 | 何が存在し、誰が所有し、どこに承認・artifact境界があるかを定義する。 |
| Post-implementation acceptance | Product Brief | 実装前に定義し、実装後に確認 | 実装後にユーザー/運用者にとって何が成立しているべきかを定義する。 |
| Execution translation | Plan | run前 | 上3つを実行手順に変換し、brief参照をimmutableにsnapshotする。 |
| Post-implementation evidence | Harness / ArtifactBundle | executor実行後、review前 | 実装後の証跡として execution summary, diff, stdout/stderr, invocation, runner trace, artifact metadata を捕獲する。 |

短く言うと、Future は予測、Product は実装後の成立条件、Harness は実装後の証跡捕獲です。

公開向けの説明例は [Supervised Agent Rollout](docs/case-studies/supervised-agent-rollout.md) にあります。

## Install CLI

```bash
cd /path/to/Patchrail
brew install pipx
pipx ensurepath
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail --help
patchrail setup
patchrail start

# optional workflow backend
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
```

`patchrail` command 自体は package entrypoint として定義済みで、`scripts/install_cli.sh` はそれを `pipx` 経由で PATH に載せるだけです。`python3` が 3.12 未満の環境では、`--python "$(command -v python3.13)"` のように明示指定します。

CLI は default で人間向けの要約表示を返します。script や automation で構造化出力が必要な場合だけ `patchrail --json ...` を使います。`patchrail setup` は first-run 用の導線で、runtime config 作成、preflight summary、次の具体コマンドを返します。`patchrail setup project --title ... --description ...` は task と編集用の `future / ontology / product` brief scaffold を作成します。scaffoldを編集した後、`patchrail brief create ...` で明示的に永続化してから `patchrail plan` を作成します。`patchrail start` は TTY では interactive shell を起動し、`patchrail start --once` はホーム画面だけを描画して終了します。

## Quickstart

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)"
# deterministic local flow
patchrail setup
patchrail setup project --title "First task" --description "Describe the supervised work"
# edit the generated future/ontology/product files, then persist each edited brief
patchrail brief create --task-id <task_id> --kind future --file <future_brief_file>
patchrail brief create --task-id <task_id> --kind ontology --file <ontology_brief_file>
patchrail brief create --task-id <task_id> --kind product --file <product_brief_file>
patchrail start
patchrail start --once
patchrail config init --workflow-backend langgraph
patchrail preflight --role planner
patchrail --json status --task-id <task_id>
# live readiness checks
patchrail config init --preset real --workflow-backend local
patchrail preflight --role executor --runner auto
pytest -q
sh scripts/local_smoke_test.sh
PATCHRAIL_CONFIG_PRESET=real PATCHRAIL_AUTO_APPROVE_FALLBACK=1 sh scripts/local_smoke_test.sh
PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh
patchrail list tasks
patchrail list preflight-snapshots
patchrail list artifact-bundles --has-trace
```

`config init` は `.patchrail/config/role-policy.json` と `.patchrail/config/workflow-backend.json` を作成します。デフォルトの `local` preset は local harness を使う simulation-backed な subscription 候補を含むため、実 API や実 CLI login がなくてもローカルでフロー確認できます。`config init --preset real` は live-readiness 用の role policy を書き出し、subscription 候補の preflight を実 CLI で確認します。workflow backend は CLI-first に `config init --workflow-backend local|langgraph` で保存し、`PATCHRAIL_WORKFLOW_BACKEND` は一時 override としてだけ使います。

interactive shell では `doctor`, `list tasks`, `task create ...`, `status --task-id ...` のような既存 subcommand をそのまま打てます。`/help`, `/doctor`, `/tasks`, `/start`, `exit` も shortcut として受け付けます。

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
patchrail preflight --role executor --runner grok_runner --access-mode api
patchrail run --task-id <task_id> --runner grok_runner --access-mode api
```

Claude subscription execution も live runner で試せます。

```bash
patchrail preflight --role executor --runner claude_code --access-mode subscription
patchrail run --task-id <task_id> --runner claude_code --access-mode subscription
```

Codex subscription execution も live runner で試せます。

```bash
patchrail preflight --role executor --runner codex_runner --access-mode subscription
patchrail run --task-id <task_id> --runner codex_runner --access-mode subscription
```

planner / reviewer も auto path を持ちます。manual 入力を残したまま、`--auto` で role candidate に生成を任せられます。

```bash
patchrail config init --workflow-backend local
patchrail plan --task-id <task_id> --auto
patchrail review --run-id <run_id> --auto
patchrail review --run-id <run_id> --auto --access-mode api
```

LangGraph を使う場合は optional dependency を入れた上で backend を切り替えます。Patchrail に入るのは LangGraph runtime であり、LangGraph Studio は必須ではありません。Studio は graph 可視化・実行・デバッグ用の UI で、Patchrail の canonical control plane には入りません。

```bash
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
patchrail config init --workflow-backend langgraph
patchrail plan --task-id <task_id> --auto
```

現在の LangGraph backend は planner / reviewer に対して stateless な 4-node graph を使います。

- planner: `collect_plan_context -> generate_plan -> validate_plan -> finalize_plan`
- reviewer: `collect_review_context -> generate_review -> validate_review -> finalize_review`

各 auto record には `workflow_metadata.node_trace`, `graph_version`, `checkpointer`, `delegate_backend` が補助情報として残ります。

artifact bundle には path map に加えて manifest-style metadata も残ります。各 artifact entry は `logical_kind`, `media_type`, `collection_status`, `sha256`, `size_bytes` を持ち、runner が structured trace を返した場合は `trace.json` として一緒に保存されます。`status --task-id ...` は `latest_artifact_bundle` まで返し、`list artifact-bundles [--task-id ...] [--logical-kind ...] [--has-trace]` で artifact history を read-side から辿れます。

現時点では、auto generation の live support は次です。

- planner: `claude subscription`, `codex api`
- reviewer: `codex subscription`, `claude api`
- executor: `codex subscription`, `claude subscription`, `codex api`, `claude api`, `grok api`

`codex subscription` は reviewer / executor path では live support に入りました。planner の auto generation backend では引き続き既定採用していません。

cross-provider または cross-access-mode の fallback が必要になった場合、Patchrail は fallback request を自動生成し、`patchrail approve-fallback --task-id ...` または `patchrail reject-fallback --task-id ...` で明示決定を要求します。

ローカルストアを直接開かなくても、`patchrail list tasks|plans|runs|reviews|approvals|fallback-requests|preflight-snapshots|artifact-bundles` で主要レコードを一覧できます。

## Docs

- [Architecture](docs/architecture.md)
- [MVP](docs/mvp.md)
- [Local Testing](docs/local-testing.md)
- [Backlog](docs/backlog.md)
- [Changelog](CHANGELOG.md)
- [Agents Contract](AGENTS.md)

## License

MIT. See [LICENSE](LICENSE).
