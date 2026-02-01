#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Deep Research Agent - 自動調査スクリプト

このスクリプトは、GoogleのGemini Deep Research Agentを使用して、
特定のテーマについて自律的に調査し、構造化されたレポートを生成します。

使用方法:
    python deep_research_agent.py [調査テーマ]

必要な環境変数:
    GOOGLE_API_KEY: Google AI StudioのAPIキー

使用例
python deep_research_agent.py "たった一日で儲かる社長に生まれ変わるの書籍について書評やレビューや口コミやブログから内容を調査洗い出して"
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

# ============================================================
# google-genaiライブラリのインポート
# バージョン1.55.0以降が必要です
# ============================================================
try:
    from google import genai
except ImportError:
    print("エラー: google-genaiライブラリがインストールされていません。")
    print("以下のコマンドでインストールしてください:")
    print("  pip install google-genai>=1.55.0")
    sys.exit(1)


# ============================================================
# 設定クラス
# 調査の各種パラメータを管理します
# ============================================================
@dataclass
class ResearchConfig:
    """調査設定を管理するデータクラス"""

    # 使用するDeep Researchモデル（推論コア）
    model_name: str = "deep-research-pro-preview-12-2025"

    # ポーリング間隔（秒）- 10〜20秒の範囲で設定
    polling_interval: int = 15

    # 最大調査時間（秒）- デフォルト15分
    max_timeout: int = 900

    # 出力ディレクトリ
    output_dir: str = "output"

    # 出力ファイル名（拡張子なし）
    output_filename: str = "report"

    # 出力言語設定（"ja"=日本語, "en"=英語, None=指定なし）
    output_language: Optional[str] = "ja"


# ============================================================
# 調査結果を格納するデータクラス
# ============================================================
@dataclass
class ResearchResult:
    """調査結果を構造化して格納するデータクラス"""

    # 調査テーマ
    query: str = ""

    # 調査のステータス（completed, failed, timeout）
    status: str = ""

    # 調査の概要（自動抽出）
    summary: str = ""

    # 調査の本文（完全なレポート）
    full_report: str = ""

    # 主要なソースURL（抽出された引用元）
    source_urls: list = field(default_factory=list)

    # 結論（自動抽出）
    conclusion: str = ""

    # 調査開始時刻
    started_at: str = ""

    # 調査完了時刻
    completed_at: str = ""

    # 調査にかかった時間（秒）
    duration_seconds: float = 0.0

    # エラーメッセージ（該当する場合）
    error_message: str = ""


# ============================================================
# Deep Research Agent クラス
# ============================================================
class DeepResearchAgent:
    """
    Gemini Deep Research Agentを操作するクラス

    このクラスは以下の機能を提供します：
    - 非同期での調査開始
    - ステータスのポーリング
    - タイムアウト処理
    - エラーハンドリング
    - 結果の構造化出力
    """

    def __init__(self, config: Optional[ResearchConfig] = None):
        """
        エージェントの初期化

        Args:
            config: 調査設定（省略時はデフォルト設定を使用）
        """
        # 設定の読み込み
        self.config = config or ResearchConfig()

        # APIキーの取得と検証
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "環境変数 GOOGLE_API_KEY が設定されていません。\n"
                "Google AI Studioからキーを取得し、以下のように設定してください:\n"
                "  export GOOGLE_API_KEY='your-api-key'"
            )

        # Google GenAIクライアントの初期化
        # api_keyを指定してクライアントを作成します
        self.client = genai.Client(api_key=self.api_key)

        # 出力ディレクトリの作成
        os.makedirs(self.config.output_dir, exist_ok=True)

    def _build_query_with_language(self, query: str) -> str:
        """
        言語設定に基づいてクエリに言語指示を追加する

        Args:
            query: 元の調査テーマ

        Returns:
            str: 言語指示が追加されたクエリ
        """
        language_instructions = {
            "ja": "【重要】レポートは必ず日本語で作成してください。",
            "en": "[IMPORTANT] Please write the report in English.",
            "zh": "[重要] 请用中文撰写报告。",
            "ko": "[중요] 보고서를 한국어로 작성해 주세요.",
        }

        if self.config.output_language and self.config.output_language in language_instructions:
            instruction = language_instructions[self.config.output_language]
            return f"{instruction}\n\n{query}"

        return query

    def research(self, query: str) -> ResearchResult:
        """
        調査を実行するメインメソッド

        このメソッドは以下の処理を行います：
        1. 非同期で調査を開始
        2. 完了までポーリング
        3. 結果を構造化して返却

        Args:
            query: 調査テーマ（日本語可）

        Returns:
            ResearchResult: 構造化された調査結果

        Raises:
            TimeoutError: 最大調査時間を超えた場合
            RuntimeError: 調査が失敗した場合
        """
        result = ResearchResult(
            query=query,
            started_at=datetime.now().isoformat()
        )

        print("=" * 60)
        print("🔬 Gemini Deep Research Agent - 調査開始")
        print("=" * 60)
        print(f"\n📋 調査テーマ:\n   {query}\n")
        print(f"⚙️  使用モデル: {self.config.model_name}")
        print(f"⏱️  最大調査時間: {self.config.max_timeout // 60}分")
        print(f"🔄 ポーリング間隔: {self.config.polling_interval}秒")
        language_names = {"ja": "日本語", "en": "英語", "zh": "中国語", "ko": "韓国語"}
        lang_display = language_names.get(self.config.output_language, "指定なし")
        print(f"🌐 出力言語: {lang_display}")
        print("-" * 60)

        start_time = time.time()

        try:
            # ============================================================
            # ステップ1: 非同期で調査を開始
            # background=True を指定することで、すぐにinteraction IDが返され、
            # サーバー側で調査が非同期に実行されます
            # ============================================================
            print("\n🚀 調査を開始しています...")

            # 言語設定に基づいてクエリに言語指示を追加
            effective_query = self._build_query_with_language(query)

            initial_interaction = self.client.interactions.create(
                input=effective_query,
                agent=self.config.model_name,
                background=True  # 非同期実行を有効化
            )

            interaction_id = initial_interaction.id
            print(f"✅ 調査開始成功！")
            print(f"   Interaction ID: {interaction_id}")

            # ============================================================
            # ステップ2: ポーリングループ
            # 調査が完了するまで定期的にステータスを確認します
            # ============================================================
            print("\n⏳ 調査中... (完了までしばらくお待ちください)")

            iteration = 0
            while True:
                iteration += 1
                elapsed_time = time.time() - start_time

                # タイムアウトチェック
                if elapsed_time > self.config.max_timeout:
                    result.status = "timeout"
                    result.error_message = f"調査が最大時間({self.config.max_timeout}秒)を超過しました"
                    raise TimeoutError(result.error_message)

                # ステータス確認
                # client.interactions.getでinteraction_idを指定して現在の状態を取得
                current_interaction = self.client.interactions.get(id=interaction_id)
                status = current_interaction.status

                # 進捗表示
                elapsed_min = int(elapsed_time // 60)
                elapsed_sec = int(elapsed_time % 60)
                print(f"   [{elapsed_min:02d}:{elapsed_sec:02d}] ポーリング #{iteration}: ステータス = {status}")

                # ============================================================
                # ステータス別の処理
                # - COMPLETED: 調査完了
                # - FAILED: 調査失敗
                # - PROCESSING/PENDING: 処理中（続行）
                # ============================================================
                if status.upper() == "COMPLETED":
                    print("\n✅ 調査が完了しました！")
                    result.status = "completed"

                    # --- 修正箇所：結果の抽出ロジックを最新仕様に合わせる ---
                    # 1. まず outputs (複数形) リストを確認
                    if hasattr(current_interaction, 'outputs') and current_interaction.outputs:
                        # 最後の出力に最終レポートが入っているのが一般的です
                        result.full_report = current_interaction.outputs[-1].text
                    
                    # 2. outputs がなかった場合の予備（古い仕様や例外への対応）
                    elif hasattr(current_interaction, 'result'):
                        result.full_report = str(current_interaction.result)
                    
                    # 3. それでも取れなかった場合の最後の手段（元々のロジック）
                    elif hasattr(current_interaction, 'output') and current_interaction.output:
                        if hasattr(current_interaction.output, 'text'):
                            result.full_report = current_interaction.output.text
                        else:
                            result.full_report = str(current_interaction.output)

                    # 万が一中身が空だった場合の処理
                    if not result.full_report:
                        result.full_report = "調査は完了しましたが、レポート本文を取得できませんでした。"
                    
                    break # ループを抜ける

                elif status.upper() == "FAILED":
                    result.status = "failed"
                    error_msg = "調査が失敗しました"
                    if hasattr(current_interaction, 'error'):
                        error_msg = f"調査が失敗しました: {current_interaction.error}"
                    result.error_message = error_msg
                    raise RuntimeError(result.error_message)

                # 処理中の場合は待機
                time.sleep(self.config.polling_interval)

        except TimeoutError:
            print(f"\n⚠️ タイムアウト: {result.error_message}")
            raise

        except RuntimeError:
            print(f"\n❌ エラー: {result.error_message}")
            raise

        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            print(f"\n❌ 予期しないエラーが発生しました: {e}")
            raise

        finally:
            # 終了時刻と所要時間を記録
            result.completed_at = datetime.now().isoformat()
            result.duration_seconds = time.time() - start_time

        # ============================================================
        # ステップ3: 結果の構造化
        # レポートから概要、ソースURL、結論を抽出します
        # ============================================================
        if result.full_report:
            result = self._extract_structured_data(result)

        return result

    def _extract_structured_data(self, result: ResearchResult) -> ResearchResult:
        """
        レポートから構造化データを抽出する

        レポート本文から以下の情報を抽出します：
        - 概要（最初の段落または要約セクション）
        - ソースURL（引用されているリンク）
        - 結論（結論セクションまたは最後の段落）

        Args:
            result: 調査結果オブジェクト

        Returns:
            ResearchResult: 構造化データが追加された結果
        """
        report = result.full_report

        # URLの抽出（Markdown形式のリンクとプレーンURL）
        # パターン1: [テキスト](URL)
        markdown_urls = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', report)
        # パターン2: プレーンURL
        plain_urls = re.findall(r'(?<!\()(https?://[^\s\)\]]+)', report)

        # 重複を除去してソースURLリストを作成
        seen_urls = set()
        for text, url in markdown_urls:
            if url not in seen_urls:
                result.source_urls.append({"title": text, "url": url})
                seen_urls.add(url)

        for url in plain_urls:
            if url not in seen_urls:
                result.source_urls.append({"title": "", "url": url})
                seen_urls.add(url)

        # 概要の抽出（最初の段落または「概要」セクション）
        summary_match = re.search(
            r'(?:##?\s*(?:概要|要約|Summary|Overview)[:\s]*\n)(.*?)(?=\n##|\n\n\n|$)',
            report,
            re.DOTALL | re.IGNORECASE
        )
        if summary_match:
            result.summary = summary_match.group(1).strip()
        else:
            # 最初の段落を概要として使用
            paragraphs = report.split('\n\n')
            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('#') and len(p) > 50:
                    result.summary = p[:500] + ('...' if len(p) > 500 else '')
                    break

        # 結論の抽出
        conclusion_match = re.search(
            r'(?:##?\s*(?:結論|まとめ|Conclusion|Summary)[:\s]*\n)(.*?)(?=\n##|\Z)',
            report,
            re.DOTALL | re.IGNORECASE
        )
        if conclusion_match:
            result.conclusion = conclusion_match.group(1).strip()
        else:
            # 最後の段落を結論として使用
            paragraphs = [p.strip() for p in report.split('\n\n') if p.strip()]
            if paragraphs:
                last_para = paragraphs[-1]
                if not last_para.startswith('#') and len(last_para) > 50:
                    result.conclusion = last_para

        return result

    def save_markdown(self, result: ResearchResult, filename: Optional[str] = None) -> str:
        """
        調査結果をMarkdown形式で保存する

        Args:
            result: 調査結果
            filename: 出力ファイル名（省略時は設定のデフォルト値を使用）

        Returns:
            str: 保存したファイルのパス
        """
        filename = filename or self.config.output_filename
        filepath = os.path.join(self.config.output_dir, f"{filename}.md")

        # Markdownヘッダーを作成
        header = f"""# 調査レポート

**調査テーマ**: {result.query}

**調査日時**: {result.started_at}

**所要時間**: {result.duration_seconds:.1f}秒

**ステータス**: {result.status}

---

"""

        # 本文を結合
        content = header + result.full_report

        # ソースURL一覧を追加（レポートに含まれていない場合）
        if result.source_urls and "## 参考文献" not in content and "## References" not in content:
            content += "\n\n---\n\n## 参考文献\n\n"
            for i, source in enumerate(result.source_urls, 1):
                title = source.get("title", "") or f"ソース {i}"
                url = source.get("url", "")
                content += f"{i}. [{title}]({url})\n"

        # ファイルに保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n📄 Markdownレポートを保存しました: {filepath}")
        return filepath

    def save_json(self, result: ResearchResult, filename: Optional[str] = None) -> str:
        """
        調査結果をJSON形式で保存する

        後続処理（DB保存など）を考慮した構造化形式で出力します。

        Args:
            result: 調査結果
            filename: 出力ファイル名（省略時は設定のデフォルト値を使用）

        Returns:
            str: 保存したファイルのパス
        """
        filename = filename or self.config.output_filename
        filepath = os.path.join(self.config.output_dir, f"{filename}.json")

        # dataclassを辞書に変換
        data = asdict(result)

        # JSONファイルに保存（日本語を正しく表示するためensure_ascii=False）
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"📊 JSONレポートを保存しました: {filepath}")
        return filepath


# ============================================================
# メイン関数
# ============================================================
def main():
    """
    メイン実行関数

    コマンドライン引数から調査テーマを受け取り、
    調査を実行して結果を保存します。
    """
    # デフォルトの調査テーマ
    default_query = (
        "日本の農業における生成AI活用事例（スマート農業、病害虫診断、自動収穫など）を、"
        "企業や自治体のプレスリリースなどの一次情報を中心に多角的に調査し、"
        "引用元を明記したレポートを作成して。"
    )

    # コマンドライン引数から調査テーマを取得
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = default_query
        print("💡 調査テーマが指定されていないため、デフォルトのテーマを使用します。")
        print("   カスタムテーマを使用するには:")
        print("   python deep_research_agent.py \"調査テーマ\"")
        print()

    try:
        # 設定を作成（必要に応じてカスタマイズ可能）
        # output_language: "ja"=日本語, "en"=英語, "zh"=中国語, "ko"=韓国語, None=指定なし
        config = ResearchConfig(
            polling_interval=15,      # 15秒ごとにポーリング
            max_timeout=900,          # 最大15分
            output_dir="output",      # 出力ディレクトリ
            output_filename="report", # 出力ファイル名
            output_language="ja"      # 出力言語（日本語）
        )

        # エージェントを初期化
        agent = DeepResearchAgent(config)

        # 調査を実行
        result = agent.research(query)

        # 結果を保存
        agent.save_markdown(result)
        agent.save_json(result)

        # 完了メッセージ
        print("\n" + "=" * 60)
        print("🎉 調査が正常に完了しました！")
        print("=" * 60)
        print(f"\n📁 出力ファイル:")
        print(f"   - {config.output_dir}/{config.output_filename}.md")
        print(f"   - {config.output_dir}/{config.output_filename}.json")

        # 概要を表示
        if result.summary:
            print(f"\n📝 概要:\n{result.summary[:300]}...")

        # ソースURL数を表示
        print(f"\n🔗 抽出されたソースURL: {len(result.source_urls)}件")

    except ValueError as e:
        print(f"\n❌ 設定エラー: {e}")
        sys.exit(1)

    except TimeoutError as e:
        print(f"\n⏱️ タイムアウト: {e}")
        print("   ヒント: config.max_timeoutの値を増やしてみてください")
        sys.exit(2)

    except RuntimeError as e:
        print(f"\n❌ 調査失敗: {e}")
        sys.exit(3)

    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(4)


if __name__ == "__main__":
    main()
