from typing import Generator

from neollm.exceptions import ContentFilterError
from neollm.types import Messages
from neollm.utils.preprocess import optimize_token

from api.domain.models.bot import ResponseSystemPrompt, ResponseSystemPromptHidden
from api.domain.models.data_point import DataPoint
from api.domain.models.llm.model import ModelName
from api.domain.services.llm import (
    ResponseGeneratorInput,
    ResponseGeneratorOutput,
    ResponseGeneratorOutputToken,
    ResponseGeneratorStreamOutput,
)
from api.infrastructures.llm.libs.response_generator.prompt import AssistantRgPrompt
from api.libs.exceptions import BadRequest

from ..base_myllm import BaseMyLLM
from ..constants import CONTENT_FILTER_NOTION

DATA_POINT_TOKEN_LIMIT = 5000
MAX_RESPONSE_TOKENS = 1024

WEB_BROWSING_RESULT = "Web検索結果"
WEB_SEARCH_FROM_URL_RESULT = "URL"


ATTACHMENT = "添付ファイル"
DOCUMENT = "ドキュメント"
QUESTION_ANSWER = "Q&A集"
USER_INPUT = "ユーザーからの指示"


class AssistantResponseGenerator(BaseMyLLM[ResponseGeneratorInput, ResponseGeneratorOutput]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.used_data_points: list[DataPoint] = []

    def _create_system_prompt(
        self,
        model: ModelName,
        tenant_name: str,
        response_system_prompt: ResponseSystemPrompt | None,
        response_system_prompt_hidden: ResponseSystemPromptHidden | None,
        terms_dict: dict[str, str],
        has_attachments: bool,
        has_data_points_from_web: bool,
        has_data_points_from_question_answer: bool,
    ) -> str:
        assistant_rg_prompt = AssistantRgPrompt(
            tenant_name=tenant_name,
            response_system_prompt=response_system_prompt,
            response_system_prompt_hidden=response_system_prompt_hidden,
            terms_dict=terms_dict,
            has_attachments=has_attachments,
            has_data_points_from_web=has_data_points_from_web,
            has_data_points_from_question_answer=has_data_points_from_question_answer,
        )
        if model.is_gpt():
            return assistant_rg_prompt.gpt()
        if model.is_claude():
            return assistant_rg_prompt.claude()
        if model.is_gemini():
            return assistant_rg_prompt.gemini()
        raise ValueError(f"model: {model} is not supported.")

    def _preprocess(self, inputs: ResponseGeneratorInput) -> Messages:
        # Messagesを作成 ---------------------------------------------------
        messages: Messages = []

        # system prompt ---------------------------------------------------
        system_prompt = self._create_system_prompt(
            model=inputs.model,
            tenant_name=inputs.tenant_name,
            response_system_prompt=inputs.response_system_prompt,
            response_system_prompt_hidden=inputs.response_system_prompt_hidden,
            terms_dict=inputs.terms_dict.root,
            has_attachments=len(inputs.attachments) > 0,
            has_data_points_from_web=len(inputs.data_points_from_web) > 0,
            has_data_points_from_question_answer=len(inputs.data_points_from_question_answer) > 0,
        )
        messages.append({"role": "system", "content": optimize_token(system_prompt)})

        # history prompt ---------------------------------------------------
        for message in inputs.messages[:-1]:
            messages.append({"role": message.role.value, "content": optimize_token(message.content.root)})

        # last user prompt ---------------------------------------------------
        data_points_from_internal = self._trim_data_points(inputs.data_points_from_internal, DATA_POINT_TOKEN_LIMIT)
        document_text = "\n".join(
            [
                f"[cite:{data_point.cite_number.root}]: {data_point.content.root}"
                for data_point in data_points_from_internal
            ]
        )
        self.used_data_points.extend(data_points_from_internal)

        user_prompt = ""

        # アタッチメントがある場合のユーザープロンプトの追加
        if len(inputs.attachments) > 0:
            user_prompt += f"<{ATTACHMENT}>\n"
            for attachment in inputs.attachments:
                if "user" in attachment:
                    user_prompt += f"```{attachment['user'].name.root}\n{self.llm.slice_text(attachment['user'].content.root, 0, inputs.max_attachment_token.root)}\n```\n"
            user_prompt += f"</{ATTACHMENT}>\n\n"

        # Web検索使用時の処理
        if len(inputs.data_points_from_web) > 0:
            user_prompt += f"<{WEB_BROWSING_RESULT}>\n"
            for data_point in inputs.data_points_from_web:
                user_prompt += f"[cite:{data_point.cite_number.root}]: {data_point.content.root}\n"
            user_prompt += f"</{WEB_BROWSING_RESULT}>\n\n"
            self.used_data_points.extend(inputs.data_points_from_web)

        # FAQ検索使用時の処理
        if len(inputs.data_points_from_question_answer) > 0:
            user_prompt += f"<{QUESTION_ANSWER}>\n"
            for data_point in inputs.data_points_from_question_answer:
                user_prompt += f"[cite:{data_point.cite_number.root}]: {data_point.content.root}\n"
            user_prompt += f"</{QUESTION_ANSWER}>\n\n"
            self.used_data_points.extend(inputs.data_points_from_question_answer)

        question_text = inputs.messages[-1].content.root
        user_prompt += (
            f"""<{DOCUMENT}>\n{document_text}\n</{DOCUMENT}>\n\n<{USER_INPUT}>\n{question_text}\n</{USER_INPUT}>"""
        )

        messages.append({"role": "user", "content": optimize_token(user_prompt)})

        # trim --------------------------------------------------
        message = self.trim_message(
            messages,
            max_response_tokens=MAX_RESPONSE_TOKENS,
            context_window=self.llm.context_window,
        )
        return message

    def _trim_data_points(self, data_points: list[DataPoint], max_tokens: int) -> list[DataPoint]:
        """data_pointsのトークン数を調整する

        Args:
            data_points (list[DataPoint]): data_points
            max_tokens (int): 最大トークン数

        Returns:
            list[DataPoint]: トークン数調整を行ったdata_points
        """
        data_points_filtered: list[DataPoint] = []
        sum_chunk_tokens = 0
        for data_point in data_points:
            sum_chunk_tokens += self.llm.count_tokens([{"role": "user", "content": data_point.content.root}])
            if sum_chunk_tokens > max_tokens:
                break
            data_points_filtered.append(data_point)
        return data_points_filtered

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
