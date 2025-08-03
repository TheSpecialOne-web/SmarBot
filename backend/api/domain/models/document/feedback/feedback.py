from typing import Optional

from pydantic import BaseModel, StrictInt

from ...user import Id as UserId
from ..document import Id as DocumentId
from .evaluation import Evaluation


class DocumentFeedback(BaseModel):
    user_id: UserId
    document_id: DocumentId
    evaluation: Optional[Evaluation] = None


class DocumentFeedbackSummary(DocumentFeedback):
    total_good: StrictInt
