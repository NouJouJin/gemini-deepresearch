# Gemini Deep Research Agent

GoogleのGemini Deep Research Agentを使用して、特定のテーマについて自律的に調査し、構造化されたレポートを生成するPythonスクリプトです。

## 機能

- **非同期実行とポーリング**: バックグラウンドで調査を実行し、定期的にステータスを確認
- **複数テーマの並列調査**: `--batch`オプションで複数の調査を同時に実行
- **出力言語設定**: 日本語、英語、中国語、韓国語に対応
- **トークン使用量の可視化**: APIのトークン消費量を表示（推定値にも対応）
- **エラーハンドリング**: 失敗時とタイムアウト時の適切な例外処理
- **構造化出力**: Markdown形式とJSON形式の両方でレポートを出力
- **ソースURL抽出**: レポートから引用元URLを自動抽出
- **ユニークなファイル名**: `調査内容の冒頭10文字_日時` 形式で上書き防止

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. APIキーの設定

Google AI StudioからAPIキーを取得し、以下のいずれかの方法で設定します。

#### 方法1: .envファイルを使用（推奨）

毎回APIキーを入力する手間が省けます。

```bash
# .env.exampleをコピーして.envを作成
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# GOOGLE_API_KEY=your-api-key-here
```

#### 方法2: 環境変数を設定

```bash
export GOOGLE_API_KEY='your-api-key-here'
```

APIキーは [Google AI Studio](https://aistudio.google.com/apikey) から取得できます。

## 使用方法

### 単一テーマの調査

```bash
# デフォルトのテーマで調査を実行
python deep_research_agent.py

# カスタムテーマで調査を実行
python deep_research_agent.py "調査したいテーマをここに入力"
```

### 複数テーマの並列調査（バッチモード）

```bash
python deep_research_agent.py --batch "テーマ1" "テーマ2" "テーマ3"
```

バッチモードでは：
- すべての調査が`background=True`で同時に開始されます
- 完了したものから順にファイルが保存されます
- すべての調査が終了するまでプログラムは終了しません
- 最後にトークン使用量の合計が表示されます

### 出力例

```
============================================================
🔬 Gemini Deep Research Agent - バッチ調査開始
============================================================
📋 調査テーマ数: 3件
🌐 出力言語: 日本語
⏱️  最大調査時間: 15分

🚀 すべての調査を並列で開始しています...
   [1/3] ✅ 開始: 日本のスマート農業について調査...
   [2/3] ✅ 開始: AIによる病害虫診断の事例...
   [3/3] ✅ 開始: 自動収穫ロボットの最新動向...

📊 3件の調査が進行中...

⏳ 調査完了を待機中... (完了したものから順に保存します)
   [02:30] ポーリング #10
   📊 進行中: 2 | 完了: 1 | 失敗: 0
      ✅ 完了: 日本のスマート農業について調査... (≈12,345 tokens)

============================================================
🎉 バッチ調査完了！
============================================================

📊 結果サマリー:
   - 総調査数: 3件
   - 成功: 3件
   - 失敗/タイムアウト: 0件
   - 総所要時間: 450.2秒

🔢 トークン使用量（合計）（≈は推定値）:
   - 入力トークン: ≈1,234
   - 出力トークン: ≈35,678
   - 合計トークン: ≈36,912

📁 保存されたファイル:
   - output/日本のスマート農_20260201_143052.md (≈12,345 tokens)
   - output/日本のスマート農_20260201_143052.json
   ...
```

## 出力ファイル

調査完了後、`output/` ディレクトリに以下のファイルが生成されます：

- `{テーマ冒頭10文字}_{日時}.md` - Markdown形式のレポート
- `{テーマ冒頭10文字}_{日時}.json` - JSON形式の構造化データ

例: `日本の農業にお_20260201_143052.md`

## 設定のカスタマイズ

`ResearchConfig` クラスで以下のパラメータを調整できます：

```python
config = ResearchConfig(
    model_name="deep-research-pro-preview-12-2025",  # 使用モデル
    polling_interval=15,    # ポーリング間隔（秒）
    max_timeout=900,        # 最大調査時間（秒）= 15分
    output_dir="output",    # 出力ディレクトリ
    output_filename="report",  # 出力ファイル名（単一調査時）
    output_language="ja"    # 出力言語
)
```

### 出力言語オプション

| 値 | 言語 |
|---|------|
| `"ja"` | 日本語（デフォルト） |
| `"en"` | 英語 |
| `"zh"` | 中国語 |
| `"ko"` | 韓国語 |
| `None` | 指定なし |

## JSON出力の構造

後続処理（データベース保存など）を考慮した構造になっています：

```json
{
  "query": "調査テーマ",
  "status": "completed",
  "summary": "調査の概要...",
  "full_report": "完全なレポート本文...",
  "source_urls": [
    {"title": "ソースタイトル", "url": "https://..."},
    ...
  ],
  "conclusion": "結論...",
  "started_at": "2026-02-01T10:30:00",
  "completed_at": "2026-02-01T10:35:00",
  "duration_seconds": 300.5,
  "error_message": "",
  "token_usage": {
    "input_tokens": 1234,
    "output_tokens": 5678,
    "total_tokens": 6912,
    "is_estimated": true
  }
}
```

## トークン使用量について

- Deep Research APIはトークン情報を直接返さないため、文字数から推定しています
- 推定値には `≈` マークが付きます
- 推定ロジック:
  - 日本語・中国語・韓国語: 約1.5文字で1トークン
  - 英語・その他: 約4文字で1トークン

## エラーハンドリング

| 終了コード | 状況 |
|----------|------|
| 0 | 正常完了 |
| 1 | 設定エラー（APIキー未設定など） |
| 2 | タイムアウト |
| 3 | 調査失敗（FAILED ステータス） |
| 4 | その他の予期しないエラー |

## 注意事項

- Deep Researchは調査に時間がかかります（通常5〜15分程度）
- Interactions APIはパブリックベータ版のため、仕様が変更される可能性があります
- APIの使用には料金が発生する場合があります

## 参考リンク

- [Gemini Deep Research Agent ドキュメント](https://ai.google.dev/gemini-api/docs/deep-research)
- [Interactions API ドキュメント](https://ai.google.dev/gemini-api/docs/interactions)
- [google-genai Python SDK](https://github.com/googleapis/python-genai)
