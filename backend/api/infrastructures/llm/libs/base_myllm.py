from typing import Generator, Generic, TypeVar, final

from neollm import MyLLM
from neollm.types import Messages, Response
from pydantic import BaseModel

from api.domain.models.llm.model import ModelName

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


class BaseInput(BaseModel):
    model: ModelName


class BaseMyLLM(MyLLM[InputType, OutputType], Generic[InputType, OutputType]):
    @final
    def trim_message(self, messages: Messages, max_response_tokens: int, context_window: int) -> Messages:
        """max_tokenで引っかからないように入力のtoken数を調整する

        Args:
            messages (Messages): Messages
            max_response_tokens (int, optional): 回答に使うtoken数.
            context_window (int, optional): llmの最大入出力token数.

        Returns:
            Messages: token数調整を行ったMessages
        """
        system_message = messages[0]
        last_user_message = messages[-1]
        num_tokens_system_message = self.llm.count_tokens([system_message])
        num_tokens_last_user_message = self.llm.count_tokens([last_user_message])

        if num_tokens_system_message + num_tokens_last_user_message + max_response_tokens >= context_window:
            last_user_message = {
                "role": "user",
                "content": self.llm.slice_text(
                    last_user_message["content"],
                    0,
                    context_window - num_tokens_system_message - max_response_tokens,
                ),
            }
            return [system_message, last_user_message]

        history_messages = messages[1:-1]
        while (
            num_tokens_system_message
            + self.llm.count_tokens(history_messages)
            + num_tokens_last_user_message
            + max_response_tokens
            >= context_window
        ):
            # system -> assistantの並びになるとclaudeとgeminiでエラーが出る
            # そのため、userとassistantを必ず一緒に削除して、system -> user -> assistantの並びにする
            del history_messages[:2]

        EMPTY_MESSAGE_CONTENT_TEXT = "ファイルの添付"
        trimmed_messages = [system_message, *history_messages, last_user_message]
        trimmed_messages = [
            {
                "role": message["role"],
                # contentが空文字の場合は、ファイルの添付というメッセージを追加する
                "content": message["content"] or EMPTY_MESSAGE_CONTENT_TEXT,
            }
            for message in trimmed_messages
        ]
        return trimmed_messages

    def _preprocess(self, inputs: InputType) -> Messages:
        return super()._preprocess(inputs)

    def _postprocess(self, response: Response) -> OutputType:
        return super()._postprocess(response)

    def _ruleprocess(self, response: Response) -> OutputType | None:
        return super()._ruleprocess(response)

    def _generate(self, stream: bool) -> Generator[str, None, None]:
        return super()._generate(stream)

    def _call(self, inputs: InputType, stream: bool = False) -> Generator[str, None, OutputType]:
        return super()._call(inputs, stream)

    def __call__(self, inputs: InputType) -> OutputType:
        return super().__call__(inputs)

    def call_stream(self, inputs: InputType) -> Generator[str, None, None]:
        return super().call_stream(inputs)
