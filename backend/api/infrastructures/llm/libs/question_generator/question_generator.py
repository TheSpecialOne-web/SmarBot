from neollm.types import Messages
from neollm.utils.preprocess import optimize_token

from api.domain.models.data_point import DataPoint

from ..base_myllm import BaseMyLLM

MAX_RESPONSE_TOKENS = 1024


class QuestionGenerator(BaseMyLLM[list[DataPoint], str]):
    def default_system_prompt(self) -> str:
        prompt = (
            "あなたは質問生成器です。ユーザーから提供されたドキュメントから、「これなら答えられる」という質問を2つ生成してください。以下の注意点を考慮してください。\n"
            "\n"
            "# 注意点:\n"
            "- 提供されたドキュメントに記載されている内容に関する質問を生成してください。あなたが生成した質問をQAシステムに投げたら、必ず答えられる質問を生成してください。\n"
            "- ドキュメントは途中で切れていたり、文脈が正しくなかったりします。注意して読んでください。\n"
            "- 「この文書」「このドキュメント」などと言っても、ユーザーは理解できません。与えられたドキュメントの先頭には[]で囲まれたファイル名が示されているので、それを含めてください。\n"
            "- 生成した質問2つは、以下の例を参考に、''で区切って出力してください。\n"
        )

        few_shots = [
            {
                "user_input": """'[不動産所得に関する案内_p9-1]:（4） 簡易な方法による記載 不動産所得を有する白色申告の方については、簡易な方法による記載が認めら れています。 4 記帳のしかた 区 分 簡易な方法による記載 （1） 収入に関", "[不動産所得に関する案内]:Ⅱ青色申告制度青色申告とは、日々の取引を所定の帳簿に記帳しその帳簿に基づいて所得金額や税額を正しく計算し申告することで、所得の計算などについて有利な取扱いが受けられる制度です。青色申告をする方は、税金の面でいろいろな特典を受けることができます。1青色申告の手続これから青色申告を始める方は、青色申告を始めようとする年の3月15日まで(その年の1月16日以後に新たに事業を始めた場合は"]""",
                "bot_output": """'不動産投資に関する所得は白色申告の場合、どのように申告しますか？', '青色申告制度を利用する場合、どのような特典を受けることができますか?'""",
            }
        ]
        prompt += "\n".join(
            [
                f"[例{i+1}]\n" f"<ドキュメント>{fs['user_input']}\n" "<生成する質問>\n" f"{fs['bot_output']}\n"
                for i, fs in enumerate(few_shots)
            ]
        )
        return prompt

    def _preprocess(self, inputs: list[DataPoint]):
        DISPLAY_LIMIT = 2

        # system prompt ---------------------------------------------------
        system_prompt = self.default_system_prompt()
        # message --------------------------------------------------
        document_content = [data_point.content.root for data_point in inputs[:DISPLAY_LIMIT]]
        user_prompt = "<ドキュメント>\n[" + ", ".join(f'"{item}"' for item in document_content) + "]\n<生成する質問>"
        messages: Messages = [
            {"role": "system", "content": optimize_token(system_prompt)},
            {"role": "user", "content": optimize_token(user_prompt)},
        ]
        trimmed_messages = self.trim_message(
            messages, max_response_tokens=MAX_RESPONSE_TOKENS, context_window=self.llm.context_window
        )
        return trimmed_messages
