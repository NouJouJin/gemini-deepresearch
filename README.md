# Gemini Deep Research Agent

GoogleのGemini Deep Research Agentを使用して、特定のテーマについて自律的に調査し、構造化されたレポートを生成するPythonスクリプトです。

## 機能

- **非同期実行とポーリング**: バックグラウンドで調査を実行し、定期的にステータスを確認
- **エラーハンドリング**: 失敗時とタイムアウト時の適切な例外処理
- **構造化出力**: Markdown形式とJSON形式の両方でレポートを出力
- **ソースURL抽出**: レポートから引用元URLを自動抽出

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. APIキーの設定

Google AI StudioからAPIキーを取得し、環境変数に設定します。

```bash
export GOOGLE_API_KEY='your-api-key-here'
```

APIキーは [Google AI Studio](https://aistudio.google.com/apikey) から取得できます。

## 使用方法

### 基本的な使い方

```bash
# デフォルトのテーマで調査を実行
python deep_research_agent.py

# カスタムテーマで調査を実行
python deep_research_agent.py "調査したいテーマをここに入力"
```

### デフォルトの調査テーマ

```
日本の農業における生成AI活用事例（スマート農業、病害虫診断、自動収穫など）を、
企業や自治体のプレスリリースなどの一次情報を中心に多角的に調査し、
引用元を明記したレポートを作成して。
```

### 出力ファイル

調査完了後、`output/` ディレクトリに以下のファイルが生成されます：

- `report.md` - Markdown形式のレポート
- `report.json` - JSON形式の構造化データ

## 設定のカスタマイズ

`ResearchConfig` クラスで以下のパラメータを調整できます：

```python
config = ResearchConfig(
    model_name="deep-research-pro-preview-12-2025",  # 使用モデル
    polling_interval=15,    # ポーリング間隔（秒）
    max_timeout=900,        # 最大調査時間（秒）= 15分
    output_dir="output",    # 出力ディレクトリ
    output_filename="report"  # 出力ファイル名
)
```

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
  "started_at": "2025-01-15T10:30:00",
  "completed_at": "2025-01-15T10:35:00",
  "duration_seconds": 300.5,
  "error_message": ""
}
```

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
