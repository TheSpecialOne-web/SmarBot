from typing import Generator

from neollm.exceptions import ContentFilterError
from neollm.types import Messages
from neollm.utils.preprocess import optimize_token

from api.domain.models.data_point import DataPoint
from api.domain.models.llm import ModelName
from api.domain.services.llm import (
    ResponseGeneratorInput,
    ResponseGeneratorOutput,
    ResponseGeneratorOutputToken,
    ResponseGeneratorStreamOutput,
)
from api.infrastructures.llm.libs.response_generator.prompt import FoundationModelPrompt
from api.libs.exceptions import BadRequest

from ..base_myllm import BaseMyLLM
from ..constants import CONTENT_FILTER_NOTION

MAX_RESPONSE_TOKENS = 1024

WEB_BROWSING_RESULT = "Web検索結果"
WEB_SEARCH_FROM_URL_RESULT = "URL"
ATTACHMENT = "添付ファイル"
FILE_NAME = "ファイル名"
FILE_CONTENT = "内容"
USER_INPUT = "ユーザーからの指示"
URL_NAME = "URL"
URL_CONTENT = "内容"


class FoundationResponseGenerator(BaseMyLLM[ResponseGeneratorInput, ResponseGeneratorOutput]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.used_data_points: list[DataPoint] = []

    def _create_system_prompt(
        self,
        model: ModelName,
        tenant_name: str,
        has_attachments: bool,
        has_data_points: bool,
        has_url: bool,
        custom_intruction: str | None,
    ) -> str:
        foundation_model_prompt = FoundationModelPrompt(
            tenant_name=tenant_name,
            has_attachments=has_attachments,
            has_data_points=has_data_points,
            has_url=has_url,
            custom_intruction=custom_intruction,
        )
        if model.is_gpt():
            system_prompt = foundation_model_prompt.gpt()
        elif model.is_claude():
            system_prompt = foundation_model_prompt.claude()
        elif model.is_gemini():
            system_prompt = foundation_model_prompt.gemini()
        else:
            raise ValueError(f"model: {model} is not supported.")
        return system_prompt

    def _preprocess(self, inputs: ResponseGeneratorInput) -> Messages:
        """回答生成

        Args:
            inputs (ResponseGeneratorInput): 回答生成入力

        Returns:
            ResponseGeneratorOutput: 回答生成出力
        """
        # Messagesを作成 ---------------------------------------------------
        messages: Messages = []

        # system prompt ---------------------------------------------------
        system_prompt = self._create_system_prompt(
            model=inputs.model,
            tenant_name=inputs.tenant_name,
            has_attachments=len(inputs.attachments) > 0,
            has_url=len(inputs.data_points_from_url) > 0,
            has_data_points=len(inputs.data_points_from_web) > 0,
            custom_intruction=(
                inputs.response_system_prompt.root if inputs.response_system_prompt is not None else None
            ),
        )
        messages.append({"role": "system", "content": optimize_token(system_prompt)})

        # history prompt ---------------------------------------------------
        for message in inputs.messages[:-1]:
            messages.append({"role": message.role.value, "content": optimize_token(message.content.root)})

        # user prompt ---------------------------------------------------
        user_prompt = f"""<{USER_INPUT}>\n{inputs.messages[-1].content.root}\n</{USER_INPUT}>\n\n"""

        # ファイル添付時の処理
        attachment_text = ""
        if len(inputs.attachments) > 0:
            attachment_text += f"<{ATTACHMENT}>\n"
            for attachment in inputs.attachments:
                if "user" in attachment:
                    attachment_text += f"<{FILE_NAME}>\n{attachment['user'].name.root}\n</{FILE_NAME}>\n<{FILE_CONTENT}>\n{self.llm.slice_text(attachment['user'].content.root, 0, inputs.max_attachment_token.root)}\n</{FILE_CONTENT}>\n"
            attachment_text += f"</{ATTACHMENT}>\n\n"

        # Web検索使用時の処理
        data_points_text = ""
        if len(inputs.data_points_from_web) > 0:
            data_points_text += f"<{WEB_BROWSING_RESULT}>\n"
            for data_point in inputs.data_points_from_web:
                data_points_text += f"[cite:{data_point.cite_number.root}]: {data_point.content.root}\n"
            data_points_text += f"</{WEB_BROWSING_RESULT}>\n\n"
            self.used_data_points.extend(inputs.data_points_from_web)

        # URL検索時の処理
        data_points_from_url_text = ""
        if len(inputs.data_points_from_url) > 0:
            data_points_from_url_text += f"<{WEB_SEARCH_FROM_URL_RESULT}>\n"
            for data_point in inputs.data_points_from_url:
                data_points_from_url_text += f"<{URL_NAME}>\n{data_point.url.root}\n</{URL_NAME}>\n<{URL_CONTENT}>\n{self.llm.slice_text(data_point.content.root, 0, inputs.max_attachment_token.root)}\n</{URL_CONTENT}>\n"
            data_points_from_url_text += f"</{WEB_SEARCH_FROM_URL_RESULT}>\n"
        messages.append(
            {
                "role": "user",
                "content": optimize_token(
                    user_prompt + attachment_text + data_points_text + data_points_from_url_text,
                ),
            }
        )

        # trim message ---------------------------------------------------
        messages = self.trim_message(
            messages,
            max_response_tokens=MAX_RESPONSE_TOKENS,
            context_window=self.llm.context_window,
        )

        return messages

    def generate_response_stream(
        self, inputs: ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        """

        Args:
            inputs (ResponseGeneratorInput): クエリ生成の入力(question, tenant_name, search_method)

        Yields:
            Generator[str, None, ResponseGeneratorOutput]: クエリ生成の出力(query, is_vector_query)
        """
        it = super().call_stream(inputs)
        try:
            for i, chunk in enumerate(it):
                # NOTE: call_streamを実行しないとused_data_pointsが更新されないため、最初のchunkでused_data_pointsを返す
                # 先に返さないと、フロントの表示がおかしくなる
                if i == 0:
                    yield self.used_data_points
                yield chunk
        except ContentFilterError:
            raise BadRequest(CONTENT_FILTER_NOTION)
        yield ResponseGeneratorOutputToken(
            input_token=self.token.input,
            output_token=self.token.output,
        )
