# Patchrail Resume Positioning

## 30秒説明

Patchrail は、Claude / Codex / Cursor などの AI コーディングワークフローの出力に対して、「何を依頼し、何が実行され、どの検証を通し、人間が何を根拠に承認したか」をローカルに記録する CLI ツールです。単なるエージェント実行基盤ではなく、AI が書いたコードをレビュー・承認できる状態にするための verification / approval packet に焦点を当てています。

## 職務経歴書向け要約

AI コーディングエージェントの実行結果を監査可能にする local-first CLI「Patchrail」を個人開発。タスク、計画、実行、検証、レビュー、承認を明示的なローカルレコードとして保存し、`patchrail verify` による検証コマンド実行結果と `patchrail packet` による承認用 Markdown / JSON パケット生成を実装。CLI 設計、状態遷移、ファイル永続化、テスト、wheel build / CLI 配布準備まで一貫して担当。

## 技術的に話すポイント

- CLI-first / headless-core-first の設計により、ダッシュボードより先に再現可能なローカル状態管理を優先。
- `Task -> Plan -> Run -> ReviewResult -> ApprovalRecord` の canonical lifecycle を維持し、verification は証跡として追加することでスコープを膨らませすぎない設計にした。
- `.patchrail/` 以下に JSON / JSONL / stdout / stderr を保存し、将来のセッションがディスクだけから安全に再開できるようにした。
- provider を汎用 model wrapper に潰さず、planner / reviewer / executor として役割分離した。
- `pytest`、smoke test、release check、wheel install 確認まで含め、ポートフォリオとして動作証明できる状態にした。

## 面接での補足

Patchrail で一番重視したのは、「AI にもっとコードを書かせること」ではなく、「AI が書いたコードを人間が責任を持って承認できる状態にすること」です。AI コーディングでは生成速度よりも、レビュー待ち、検証不足、権限境界、複数エージェント出力の管理が実務上のボトルネックになります。そこで v0.2 では generic orchestration ではなく、verification と approval packet に絞りました。

## 代表作として見せる順番

1. README の冒頭で product thesis を説明する。
2. 3分デモで `verify -> review-queue -> packet` の流れを見せる。
3. PR で設計意図、テスト、release check が残っていることを見せる。
4. 面接では「なぜ dashboard ではなく CLI / local-first から始めたか」を説明する。
5. 最後に、今後の改善として verification preset、diff evidence、approval packet の品質向上を話す。

## 短い職務経歴書用文面

AI コーディングエージェントの実行結果を検証・承認可能にする local-first CLI「Patchrail」を設計・実装。`patchrail verify` で検証コマンドの stdout / stderr / exit code / elapsed time を保存し、`patchrail packet` でタスク、計画、実行、成果物、検証、レビュー、承認をまとめた approval packet を生成。状態遷移設計、ファイル永続化、CLI UX、テスト、wheel build / CLI 配布準備まで担当。
