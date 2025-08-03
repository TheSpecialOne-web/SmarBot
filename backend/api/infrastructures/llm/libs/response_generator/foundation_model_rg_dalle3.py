from typing import Generator

from neollm.exceptions import ContentFilterError
from neollm.types import Messages
from neollm.utils.preprocess import optimize_token

from api.domain.services.llm import (
    Dalle3ResponseGeneratorInput,
    Dalle3ResponseGeneratorOutput,
    ResponseGeneratorOutputToken,
    ResponseGeneratorStreamOutput,
)
from api.libs.exceptions import BadRequest

from ..base_myllm import BaseMyLLM
from ..constants import CONTENT_FILTER_NOTION

MAX_RESPONSE_TOKENS = 1024

GENERATED_IMAGE = "画像"
USER_INPUT = "ユーザーからの指示"
BOT_OUTPUT = "生成する文章"


class ResponseGeneratorForDalle3(BaseMyLLM[Dalle3ResponseGeneratorInput, Dalle3ResponseGeneratorOutput]):
    def _get_default_system_prompt(
        self,
    ) -> str:
        prompt = (
            "あなたは画像の説明文生成器です。\n"
            "ユーザーから作成して欲しい画像の要件が渡されて、別のAIが画像を生成します。\n"
            "画像が生成された旨を、以下の注意点を考慮して生成してください。\n"
            "\n"
            "# 注意点:\n"
            "- ユーザーから入力される言語と同じ言語の文章を生成してください。\n"
            "- 「私は画像を生成することができません」のような文章は絶対に生成しないでください。「〜を描いて」という命令があなたに与えられることもありますが、画像の生成は別のAIが行います。画像が生成された前提で、テキストを生成してください。\n"
            "- 生成文章は、以下の「生成例」を参考にしてください。生成例のように、基本的には「{ユーザー入力}のイラストを作成しました。{追加の指示や感想を求める文章}」という構成にしてください。\n"
            "- あなたには生成された画像は与えられません。従って、生成された画像を想像したようなテキストは出力はせず、「生成例」のようにユーザーの元の文章を反復するようなテキストを出力してください。\n"
            "\n"
            "# 生成例:\n"
        )

        few_shots: list[dict[str, str | list[str]]] = [
            {
                "user_input": "[1]白髪の男性が黒板の前に立って授業をしている",
                "bot_output": "白髪の男性が黒板の前に立って授業をしているイラストを作成しました。気に入ってくれると嬉しいです。",
            },
            {
                "user_input": "[1]紅葉が周りに広がる富士山。水墨画風",
                "bot_output": "紅葉が周りに広がる富士山のイラストを、水墨画風で作成しました。追加の要件があれば教えてください。",
            },
            {
                "user_input": "[1]サッカーをするミーアキャット\n[2]サングラスをかけさせて",
                "bot_output": "サッカーをするサングラスをかけたミーアキャットのイラストを作成しました。追加の指示があれば、それに従って再度生成します。",
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

    def _preprocess(self, inputs: Dalle3ResponseGeneratorInput) -> Messages:
        """回答生成
        Args:
            inputs (Dalle3ResponseGeneratorInput): 回答生成入力
        Returns:
            Dalle3ResponseGeneratorOutput: 回答生成出力
        """

        self.image_url = inputs.image_url
        # Messagesを作成 ---------------------------------------------------
        messages: Messages = []

        # system prompt ---------------------------------------------------
        system_prompt = self._get_default_system_prompt()
        messages.append({"role": "system", "content": optimize_token(system_prompt)})

        # history prompt ---------------------------------------------------
        for message in inputs.messages[:-1]:
            messages.append({"role": message.role.value, "content": optimize_token(message.content.root)})

        # user prompt ---------------------------------------------------
        messages.append(
            {
                "role": "user",
                "content": optimize_token(inputs.messages[-1].content.root),
            }
        )

        # trim message ---------------------------------------------------
        messages = self.trim_message(
            messages=self._preprocess_messages(messages),
            max_response_tokens=MAX_RESPONSE_TOKENS,
            context_window=self.llm.context_window,
        )

        return messages

    def generate_response_stream(
        self, inputs: Dalle3ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        """
        Args:
            inputs (Dalle3ResponseGeneratorInput): クエリ生成の入力(question, tenant_name, search_method)
        Yields:
            Generator[str, None, Dalle3ResponseGeneratorOutput]: クエリ生成の出力(query, is_vector_query)
        """
        it = super().call_stream(inputs)
        try:
            for chunk in it:
                yield chunk
        except ContentFilterError:
            raise BadRequest(CONTENT_FILTER_NOTION)
        yield ResponseGeneratorOutputToken(
            input_token=self.token.input,
            output_token=self.token.output,
        )
