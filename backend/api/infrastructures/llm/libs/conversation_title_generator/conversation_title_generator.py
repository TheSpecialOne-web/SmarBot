from neollm.types import Messages, Response

from api.domain.models.conversation.conversation_turn import Turn
from api.domain.models.conversation.title import Title
from api.libs.logging import get_logger

from ..base_myllm import BaseMyLLM

QUESTION_TAG = "質問"


class ConversationTitleGenerator(BaseMyLLM[list[Turn], Title]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger()

    @property
    def system_prompt(self) -> str:
        return (
            f"生成例を参考にして、<{QUESTION_TAG}>から</{QUESTION_TAG}>で与えられるユーザーからの質問を元に、20文字以下のタイトルを生成してください。\n\n"
            "# 生成例:\n"
            "LightGBMの論文要約\n"
            "英語の作文添削\n"
            "有給休暇の申請方法\n"
            "メールの文章作成\n"
        )

    def _preprocess(self, inputs: list[Turn]) -> Messages:
        USER_INPUT_MAX_LENGTH = 2000
        MAX_RESPONSE_TOKENS = 50
        first_question = self.llm.slice_text(inputs[0].user.root, 0, USER_INPUT_MAX_LENGTH)

        messages: Messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"<{QUESTION_TAG}>{first_question}</{QUESTION_TAG}>"},
        ]

        messages = self.trim_message(
            messages,
            max_response_tokens=MAX_RESPONSE_TOKENS,
            context_window=self.llm.context_window,
        )
        return messages

    def _ruleprocess(self, inputs: list[Turn]) -> Title | None:
        if len(inputs) == 0:
            return Title()
        return None

    def _postprocess(self, response: Response) -> Title:
        try:
            return Title(root=str(response.choices[0].message.content))
        except Exception as e:
            self.logger.error("Failed to generate conversation title", exc_info=e)
            return Title()
