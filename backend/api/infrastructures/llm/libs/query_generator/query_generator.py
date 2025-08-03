import ast
import re

from neollm.exceptions import ContentFilterError
from neollm.types import Messages, Response
from neollm.utils.postprocess import strip_string
from neollm.utils.preprocess import optimize_token

from api.domain.models.query import Queries
from api.domain.services.llm import QueryGeneratorInput, QueryGeneratorOutput
from api.libs.exceptions import BadRequest

from ..base_myllm import BaseMyLLM
from ..constants import CONTENT_FILTER_NOTION

MAX_RESPONSE_TOKENS = 1024
MAX_HISTORY = 3  # 取得する過去のユーザー入力の数


class QueryGenerator(BaseMyLLM[QueryGeneratorInput, QueryGeneratorOutput]):
    def _get_user_prompt(
        self, last_user_message: str, history_user_messages: list[str], queries: list[str] | None = None
    ) -> str:
        """ユーザープロンプトの作成"""

        # タグの定義
        history_tag = "<入力履歴>"
        user_input_tag = "<ユーザー入力>"
        query_tag = "<検索クエリ>"

        # promptの作成　--------------------------------------------------
        history_user_prompt = ""
        last_user_prompt = ""
        queries_prompt = ""

        # 履歴の追加
        if len(history_user_messages):
            history_user_prompt = (
                history_tag
                + "\n"
                + "\n".join([f'"""{history_user_message}"""' for history_user_message in history_user_messages])
                + "\n"
            )

        # 最後のユーザ入力
        last_user_prompt = user_input_tag + "\n" + f'"""{last_user_message}"""' + "\n"

        # 検索クエリ
        if queries is not None and len(queries):
            queries_prompt = query_tag + "\n" + ",".join(list(queries)) + "\n"

        return history_user_prompt + last_user_prompt + queries_prompt

    def _get_default_system_prompt(self, tenant_name: str) -> str:
        # システムプロンプト
        prompt = (
            f"{tenant_name}のドキュメントやWeb検索をするために、<ユーザー入力>に含まれる質問を理解して<検索クエリ>を生成してください。\n"
            "<ユーザー入力>の理解の為に，必要に応じて<入力履歴>を参照してください。\n"
            "<検索クエリ>には，検索に必要な必要最低限の名詞のみを抽出してください。\n"
            "\n"
            "# 注意点\n"
            "以下の項目は<検索クエリ>に絶対に含めないでください。\n"
            "- 引用元のファイル名、文書名(*.txt、*.pdfなど)\n"
            "- []や<>\n"
            "- <<>>内のテキスト\n"
            "- 助詞\n"
            "- 動詞\n"
            "- 「内容」や「提案」等の抽象名詞\n"
            "- 文節"
            "\n"
            "以下の項目は<検索クエリ>に含めてください。\n"
            "- 固有名詞（人名、組織名、製品名など）\n"
            "- 特定の技術用語や専門用語\n"
            "- 数値や日付\n"
            "- 未知語\n"
            "\n"
        )

        # few-shot
        # "purpose": そのfew-shotの目的
        # ”history_user_messages”: 過去のユーザー入力
        # "last_user_message": 現在のユーザー入力
        # "queries": 検索クエリ
        few_shots: list[dict[str, list[str]]] = [
            {
                "purpose": ["履歴がない新規チャットを想定", "<検索クエリ>に含めない単語：概要，提案"],
                "history_user_messages": [],
                "last_user_message": ["ABCのプロジェクトで直面している課題の概要とその解決策を提案してください。"],
                "queries": ["ABC", "プロジェクト", "課題", "解決策"],
            },
            {
                "purpose": ["1つ前の履歴を参照", "<検索クエリ>に含めない単語：必要，手順，箇条書き"],
                "history_user_messages": ["給与所得が2,000万円を超える場合、所得税等の確定申告が必要ですか"],
                "last_user_message": [
                    "その際の確定申告の手順について教えてください。",
                    "主要な項目を箇条書きで書いてください。",
                ],
                "queries": ["給与所得", "2000万", "所得税", "確定申告"],
            },
            {
                "purpose": [
                    "別テーマを想定して1つ前の履歴を無視",
                    "<検索クエリ>に含めない単語：提示, 分類, 箇条書き, 300文字以内, 対策, 論理的",
                ],
                "history_user_messages": ["デジタル通貨への対応について、当行の方針を提示してください"],
                "last_user_message": [
                    "デジタル通貨導入に伴う具体的なリスクとその対策について記述してください。300文字以内で、主要なリスクを少なくとも3つ挙げ、それぞれに対する対策を論理的に示してください。"
                ],
                "queries": ["金融商品", "販売", "取り組み"],
            },
            {
                "purpose": ["3つ前の履歴を参照", "<検索クエリ>に含めない単語：概算，説明，優位，明示"],
                "history_user_messages": [
                    "弊社人事部の初任給の設定額の概算を知りたいです",
                    "AIエンジニアのほうも説明してください",
                    "ソフトウェアエンジニアでは？",
                ],
                "last_user_message": [
                    "2種類のエンジニアで比較を行ってください",
                    "比較した上で，どちらが優位であるかを明示してください",
                ],
                "queries": ["AIエンジニア", "ソフトウェアエンジニア", "初任給", "比較"],
            },
            {
                "purpose": ["3つ前の履歴を参照", "<検索クエリ>に含めない単語：決定"],
                "history_user_messages": [
                    "来週の営業会議の議題は決定していますか？",
                    "その会議の参加者リストを教えてください",
                    "リストの中で，人事部は何人いますか？",
                ],
                "last_user_message": ["その中に、田中さんはいますか？"],
                "queries": ["来週", "営業会議", "参加者", "人事部", "田中"],
            },
        ]

        few_shot_prompts = ""

        # few-shotをLLMに与える形に整形
        for i, few_shot in enumerate(few_shots):
            history_user_messages = few_shot["history_user_messages"]
            last_user_message = few_shot["last_user_message"][0]
            queries = few_shot["queries"]

            few_shot_prompt = (
                f"\n[例{i + 1}]\n" f"{few_shot['purpose'][0]}\n" f"{few_shot['purpose'][1]}\n\n"
            ) + self._get_user_prompt(last_user_message, history_user_messages, queries)
            few_shot_prompts += few_shot_prompt

        return prompt + few_shot_prompts

    def _preprocess(self, inputs: QueryGeneratorInput) -> Messages:
        # system prompt --------------------------------------------------
        system_prompt = (
            self._get_default_system_prompt(inputs.tenant_name.value)
            if inputs.query_system_prompt is None
            else inputs.query_system_prompt.root
        )

        # user prompt --------------------------------------------------
        user_messages = [message.content.root for message in inputs.messages if message.role == "user"]
        user_prompt = self._get_user_prompt(
            last_user_message=user_messages[-1], history_user_messages=user_messages[-1 * MAX_HISTORY - 1 : -1]
        )

        # message --------------------------------------------------
        messages: Messages = [
            {"role": "system", "content": optimize_token(system_prompt)},
            {"role": "user", "content": optimize_token(user_prompt)},
        ]

        # trim --------------------------------------------------
        message = self.trim_message(
            messages,
            max_response_tokens=MAX_RESPONSE_TOKENS,
            context_window=self.llm.context_window,
        )

        return message

    def _postprocess(self, response: Response) -> QueryGeneratorOutput:
        # Response -> str --------------------------------------------------
        _raw_content = response.choices[0].message.content
        if _raw_content is None:
            raise Exception("Failed to generate query")
        # 余分な文字列消去
        _raw_content = (
            strip_string(
                text=_raw_content,
                first_character=["<output>", "<outputs>", "<ANSWER>", "<answer>", "<回答>", "<検索クエリ>"],
            )
            .replace("</output>", "")
            .replace("</outputs>", "")
            .replace("</ANSWER>", "")
            .replace("</answer>", "")
            .replace("</回答>", "")
            .replace("</検索クエリ>", "")
        )

        # []内の文字列を取得([]がなかったら，そのまま)
        match = re.search(r"\[(.*)\]", _raw_content)
        if match:
            _raw_content = match.group(1)

        # str -> list[str] --------------------------------------------------
        try:
            _query_list_like = ast.literal_eval(_raw_content)
        except Exception:
            _query_list_like = [q.strip() for q in str(_raw_content).split(",")]
        if not isinstance(_query_list_like, list):
            search_query_list = str(_query_list_like).replace(",", " ").split(" ")
        else:
            search_query_list = [str(query) for query in _query_list_like]
        return QueryGeneratorOutput(
            queries=Queries.from_list(search_query_list),
            input_token=self.token.input,
            output_token=self.token.output,
        )

    def __call__(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        try:
            return super().__call__(inputs)
        except ContentFilterError:
            raise BadRequest(CONTENT_FILTER_NOTION)
