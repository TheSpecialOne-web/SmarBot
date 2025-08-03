from neollm.exceptions import ContentFilterError
from neollm.types import Messages, Response
from neollm.utils.postprocess import strip_string
from neollm.utils.preprocess import optimize_token

from api.domain.models.query import Queries
from api.domain.services.llm import QueryGeneratorInput, QueryGeneratorOutput
from api.libs.logging import get_logger

from ..base_myllm import BaseMyLLM

USER_INPUT = "入力"
BOT_OUTPUT = "生成するプロンプト"


class QueryGeneratorForDalle3(BaseMyLLM[QueryGeneratorInput, QueryGeneratorOutput]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger()

    def _get_default_system_prompt(self) -> str:
        prompt = (
            "あなたは画像生成プロンプトを生成するAIです。\n"
            "以下の注意点に従って、プロンプトを生成してください。生成の際は「生成例」を参考にしてください。\n"
            "\n"
            "# 注意点:\n"
            "- 日本語の文章を生成してください。\n"
            '- ユーザーからの入力は、[{"role": "user", "content": 元のプロンプト}]というlist[dict[str,str]]の形で与えられます。ユーザーからの新しい入力は、dictがappendされていきます。\n'
            "- 履歴を考慮してユーザーからの入力を処理してください。元のプロンプトの履歴は[1]~, [2]~の形で与えられ、数字が新しいものほど新しいプロンプトです。\n"
            "- 出力するプロンプトは、必ず名詞で終わるようにしてください。元の文章に「書いて」のような動詞が含まれている場合は、それを取り除いてください。\n"
            "\n"
            "# 生成例:\n"
        )

        few_shots: list[dict[str, str | list[str]]] = [
            {
                "user_input": "[1]黒髪ポニーテールのk-popアイドルを書いて。",
                "bot_output": "黒髪ポニーテールのk-popアイドル",
            },
            {
                "user_input": "[1]青髪のバンドマンを描いて\n[2]ピンク髪にして",
                "bot_output": "ピング髪のバンドマン",
            },
            {
                "user_input": "[1]ボクシングをする猫型ロボットを描いて\n[2]アニメ調にして",
                "bot_output": "ボクシングをする猫型ロボット。アニメ調",
            },
            {
                "user_input": "[1]紅葉が周りに広がる富士山を描いて\n[2]水墨画風にして",
                "bot_output": "紅葉が周りに広がる富士山。水墨画風",
            },
            {
                "user_input": "[1]ヘリコプターを運転する犬をかいて\n[2]サングラスを掛けさせて",
                "bot_output": "ヘリコプターを運転するサングラスを掛けた犬",
            },
            {
                "user_input": "[1]ダンスを踊るハムスターを描いて\n[2]ありがとうございます。アフロヘアにしてもらえますか？\n[3]いいですね。オーディエンスを増やしてください",
                "bot_output": "オーディエンスに囲まれている、ダンスを踊るハムスター",
            },
        ]

        prompt += "\n".join(
            [
                f"[例{i}]\n" f"<{USER_INPUT}>{fs['user_input']}\n" f"<{BOT_OUTPUT}>\n" f"{fs['bot_output']}\n"
                for i, fs in enumerate(few_shots, 1)
            ]
        )
        return prompt

    def _preprocess_messages(self, messages: Messages) -> Messages:
        system = messages[0]
        user_input = ""
        number = 1
        for i, message in enumerate(messages[1:]):
            if message["role"] == "user":
                user_input += f'[{number}]{message["content"]}'
                number += 1
                if i != len(messages[1:]) - 1:
                    user_input += "\n"
        return [system, {"role": "user", "content": f"<{USER_INPUT}>{user_input}\n<{BOT_OUTPUT}>"}]

    def _preprocess(self, inputs: QueryGeneratorInput) -> Messages:
        # system prompt --------------------------------------------------
        system_prompt = self._get_default_system_prompt()
        # message --------------------------------------------------
        messages: Messages = []
        messages.append({"role": "system", "content": optimize_token(system_prompt)})
        for message in inputs.messages:
            messages.append({"role": message.role.value, "content": optimize_token(message.content.root)})
        return self._preprocess_messages(messages)

    def _postprocess(self, response: Response) -> QueryGeneratorOutput:
        # Response -> str --------------------------------------------------
        _raw_content = response.choices[0].message.content
        if _raw_content is None:
            raise Exception("Failed to generate query")
        # 余分な文字列消去
        _raw_content = (
            strip_string(text=_raw_content, first_character=["<output>", "<outputs>", "<ANSWER>", "<answer>"])
            .replace("</output>", "")
            .replace("</outputs>", "")
            .replace("</ANSWER>", "")
            .replace("</answer>", "")
        )

        return QueryGeneratorOutput(
            queries=Queries.from_list([_raw_content]),
            input_token=self.token.input,
            output_token=self.token.output,
        )

    def __call__(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        try:
            return super().__call__(inputs)
        except ContentFilterError as e:
            self.logger.warning("Failed to generate query because of content filter", exc_info=e)
        except Exception as e:
            self.logger.error("Failed to generate query", exc_info=e)

        if self.inputs is None:
            raise Exception("Failed to generate query")
        return QueryGeneratorOutput(
            queries=Queries.from_list([inputs.messages[-1].content.root]),
            input_token=self.token.input,
            output_token=self.token.output,
        )
