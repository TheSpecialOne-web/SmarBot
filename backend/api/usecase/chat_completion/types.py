from typing import Generator

from pydantic import BaseModel

from api.domain.models import api_key, bot, chat_completion, tenant
from api.domain.models.chat_completion import (
    ChatCompletionDataPoint,
    ChatCompletionWithApiKeyId,
    Comment,
    Evaluation,
)
from api.libs.exceptions import BadRequest


class CreateChatCompletionInput(BaseModel):
    tenant: tenant.Tenant
    bot: bot.Bot
    api_key: api_key.ApiKey
    chat_completion: chat_completion.ChatCompletionForCreate


class UpdateChatCompletionFeedbackEvaluationInput(BaseModel):
    id: chat_completion.Id
    evaluation: Evaluation


class UpdateChatCompletionFeedbackCommentInput(BaseModel):
    id: chat_completion.Id
    comment: Comment


class CreateChatCompletionNonStreamOutput(BaseModel):
    id: chat_completion.Id
    answer: chat_completion.Content
    data_points: list[ChatCompletionDataPoint]


class ChatCompletionId(BaseModel):
    id: chat_completion.Id


class ChatCompletionAnswer(BaseModel):
    answer: chat_completion.Content


class ChatCompletionDataPoints(BaseModel):
    data_points: list[ChatCompletionDataPoint]


CreateChatCompletionStreamOutput = Generator[
    ChatCompletionId | ChatCompletionAnswer | ChatCompletionDataPoints,
    None,
    None,
]


class BotWithApiKeys(BaseModel):
    bot: bot.Bot
    api_keys: list[api_key.ApiKey]


class ChatCompletionWithBotAndApiKey(BaseModel):
    chat_completion: chat_completion.ChatCompletion
    bot: bot.Bot
    api_key: api_key.ApiKey

    @classmethod
    def from_chat_completion_and_bot_with_api_keys_list(
        cls,
        chat_completion_with_api_key_id: ChatCompletionWithApiKeyId,
        bot_with_api_keys_list: list[BotWithApiKeys],
    ) -> "ChatCompletionWithBotAndApiKey":
        # chat_completion_with_api_key_idのapi_key_idとbot_with_api_keysのapi_keyのidが一致するapi_keyを取得
        api_key = next(
            (
                key
                for bot_with_api_keys in bot_with_api_keys_list
                for key in bot_with_api_keys.api_keys
                if key.id == chat_completion_with_api_key_id.api_key_id
            ),
            None,
        )

        if api_key is None:
            raise ValueError("api_key not found")

        bot = next(
            (
                bot_with_api_keys.bot
                for bot_with_api_keys in bot_with_api_keys_list
                if bot_with_api_keys.bot.id == api_key.bot_id
            ),
            None,
        )
        if bot is None:
            raise BadRequest("bot not found")

        return ChatCompletionWithBotAndApiKey(
            chat_completion=chat_completion.ChatCompletion(
                id=chat_completion_with_api_key_id.id,
                messages=chat_completion_with_api_key_id.messages,
                answer=chat_completion_with_api_key_id.answer,
                token_count=chat_completion_with_api_key_id.token_count,
                data_points=chat_completion_with_api_key_id.data_points,
                created_at=chat_completion_with_api_key_id.created_at,
                feedback=chat_completion_with_api_key_id.feedback,
            ),
            bot=bot,
            api_key=api_key,
        )

    def to_dict(self):
        return {
            "アシスタント名": self.bot.name.value,
            "APIキー名": self.api_key.name.root,
            "リクエスト": self.chat_completion.messages.to_json(),
            "アシスタント出力": self.chat_completion.answer.root,
            "会話日時": (self.chat_completion.created_at.jst_formatted() if self.chat_completion.created_at else ""),
            "回答生成モデル": self.bot.response_generator_model_family.value,
            "総トークン数": self.chat_completion.token_count.root,
            "評価": (
                self.chat_completion.feedback.evaluation.value
                if self.chat_completion.feedback and self.chat_completion.feedback.evaluation
                else ""
            ),
            "コメント": (
                self.chat_completion.feedback.comment.root
                if self.chat_completion.feedback and self.chat_completion.feedback.comment
                else ""
            ),
        }
