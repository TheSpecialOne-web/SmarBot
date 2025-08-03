from typing import Optional

from pydantic import BaseModel, Field

from ...attachment.attachment import Attachment
from ...bot import Name as BotName
from ...document import document as document_domain
from ...document_folder import DocumentFolder
from ...group import Name as GroupName
from ...llm import ModelName
from ...question_answer import Answer, Question
from ...text_2_image_model import Text2ImageModelName
from ...token import TokenCount, TokenSet
from ...user import Name as UserName
from ..conversation_data_point.conversation_data_point import (
    ConversationDataPoint,
    ConversationDataPointWithDetail,
)
from ..id import Id as ConversationId
from .bot_output import BotOutput
from .created_at import CreatedAt
from .feedback.comment import Comment
from .feedback.evaluation import Evaluation
from .id import Id, create_id
from .message import Message
from .query import Query
from .turn import Turn
from .user_input import UserInput


class ConversationTurnProps(BaseModel):
    conversation_id: ConversationId
    user_input: UserInput
    bot_output: BotOutput
    queries: list[Query]
    token_set: TokenSet
    token_count: TokenCount
    query_generator_model: ModelName | None
    response_generator_model: ModelName
    evaluation: Optional[Evaluation] = None
    image_generator_model: Text2ImageModelName | None = None
    document_folder: Optional[DocumentFolder] = None
    comment: Optional[Comment] = None


class ConversationTurn(ConversationTurnProps):
    id: Id
    created_at: CreatedAt
    data_points: list[ConversationDataPoint]

    def to_turn(self) -> Turn:
        return Turn(
            bot=Message(root=self.bot_output.root),
            user=Message(root=self.user_input.root),
        )


class ConversationTurnWithAttachments(ConversationTurnProps):
    id: Id
    created_at: CreatedAt
    data_points: list[ConversationDataPoint]
    attachments: list[Attachment]


class ConversationTurnForCreate(ConversationTurnProps):
    id: Id = Field(default_factory=create_id)


class ConversationTurnWithUserAndBot(ConversationTurn):
    user_name: UserName
    bot_name: BotName

    def to_dict(self) -> dict[str, str]:
        return {
            "ユーザー": self.user_name.value,
            "基盤モデル/アシスタント": self.bot_name.value,
            "入力": self.user_input.root,
            "出力": self.bot_output.root,
            "会話日時": self.created_at.jst_formatted(),
            "回答生成モデル": self.response_generator_model.value,
            "総トークン数": str(self.token_count.root),
            "評価": self.evaluation.value if self.evaluation is not None else "",
            "コメント": self.comment.root if self.comment is not None else "",
        }


class ConversationTurnWithUserAndBotAndGroup(ConversationTurnProps):
    id: Id
    created_at: CreatedAt
    user_name: UserName
    bot_name: BotName
    group_names: list[GroupName]
    data_points: list[ConversationDataPointWithDetail]
    attachments: list[Attachment]

    def to_dict(self) -> dict[str, str]:
        conversation_turn = {
            "ユーザー": self.user_name.value,
            "基盤モデル/アシスタント": self.bot_name.value,
            "入力": self.user_input.root,
            "出力": self.bot_output.root,
            "会話日時": self.created_at.jst_formatted(),
            "回答生成モデル": self.response_generator_model.value,
            "総トークン数": str(self.token_count.root),
            "評価": self.evaluation.value if self.evaluation else "",
            "コメント": self.comment.root if self.comment else "",
        }

        # Adding document references
        valid_data_points_with_document = [
            (
                "/".join(
                    [
                        document_folder.name.root
                        for document_folder in sorted(
                            data_point.document_folders, key=lambda x: x.order.root, reverse=True
                        )
                        if isinstance(document_folder, DocumentFolder) and document_folder.name is not None
                    ]
                ),
                data_point.document_name.value,
                data_point.document_file_extension.value,
            )
            for data_point in self.data_points
            if data_point.document_folders is not None
            and isinstance(data_point.document_name, document_domain.Name)
            and isinstance(data_point.document_file_extension, document_domain.FileExtension)
        ]

        for doc_idx, document in enumerate(valid_data_points_with_document, start=1):
            document_full_path, document_name, document_file_extension = document
            conversation_turn[f"ドキュメント参照元{doc_idx}"] = (
                f"{document_full_path}/{document_name}.{document_file_extension}"
            )

        # Adding group names
        for group_idx, group_name in enumerate(self.group_names, start=1):
            conversation_turn[f"所属グループ{group_idx}"] = group_name.value

        # Adding FAQ
        valid_data_points_with_faq = [
            (data_point.question.root, data_point.answer.root)
            for data_point in self.data_points
            if isinstance(data_point.question, Question) and isinstance(data_point.answer, Answer)
        ]

        for faq_idx, question_answer in enumerate(valid_data_points_with_faq, start=1):
            (
                conversation_turn[f"FAQ参照元_質問{faq_idx}"],
                conversation_turn[f"FAQ参照元_回答{faq_idx}"],
            ) = question_answer

        # Adding Web references
        valid_data_points_with_web_url = [data_point for data_point in self.data_points if data_point.url.root]

        for web_idx, data_point in enumerate(valid_data_points_with_web_url, start=1):
            conversation_turn[f"Web参照元_名前{web_idx}"] = data_point.chunk_name.root
            conversation_turn[f"Web参照元_url{web_idx}"] = data_point.url.root

        # Adding Attachment references
        for attachment_idx, attachment in enumerate(self.attachments, start=1):
            conversation_turn[f"添付ファイル{attachment_idx}"] = (
                f"{attachment.name.root}.{attachment.file_extension.value}"
            )

        return conversation_turn
