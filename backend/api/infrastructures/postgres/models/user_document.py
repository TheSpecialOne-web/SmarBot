from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models.document import Id as DocumentId
from api.domain.models.document.feedback import feedback as document_feedback_domain
from api.domain.models.user import Id as UserId

from .base import BaseModel

if TYPE_CHECKING:
    from .document import Document
    from .user import User


class UserDocument(BaseModel):
    __tablename__ = "users_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)
    evaluation: Mapped[str | None] = mapped_column(Enum("good", "bad", name="user_document_evaluation"), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="documents")
    document: Mapped["Document"] = relationship("Document", back_populates="users")

    @classmethod
    def from_domain(cls, document_feedback: document_feedback_domain.DocumentFeedback) -> "UserDocument":
        return cls(
            document_id=document_feedback.document_id.value,
            user_id=document_feedback.user_id.value,
            evaluation=document_feedback.evaluation.value if document_feedback.evaluation is not None else None,
        )

    def to_domain(self) -> "document_feedback_domain.DocumentFeedback":
        return document_feedback_domain.DocumentFeedback(
            user_id=UserId(value=self.user_id),
            document_id=DocumentId(value=self.document_id),
            evaluation=document_feedback_domain.Evaluation(self.evaluation) if self.evaluation is not None else None,
        )

    def to_domain_with_summary(self, total_good: int) -> document_feedback_domain.DocumentFeedbackSummary:
        return document_feedback_domain.DocumentFeedbackSummary(
            user_id=UserId(value=self.user_id),
            document_id=DocumentId(value=self.document_id),
            evaluation=document_feedback_domain.Evaluation(self.evaluation) if self.evaluation is not None else None,
            total_good=total_good,
        )
