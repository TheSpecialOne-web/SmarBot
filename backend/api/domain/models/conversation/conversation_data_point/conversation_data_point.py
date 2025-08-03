from pydantic import Field

from ...data_point import DataPoint, DataPointWithDetail
from ...document.feedback import DocumentFeedbackSummary
from ..conversation_turn.id import Id as ConversationTurnId
from .id import Id, create_id


class ConversationDataPointPropsWithTurnId(DataPoint):
    turn_id: ConversationTurnId


class ConversationDataPoint(ConversationDataPointPropsWithTurnId):
    id: Id


class ConversationDataPointForCreate(ConversationDataPointPropsWithTurnId):
    id: Id = Field(default_factory=create_id)


class ConversationDataPointWithTotalGood(ConversationDataPoint):
    total_good: int


class ConversationDataPointWithDocumentFeedbackSummary(ConversationDataPoint):
    document_feedback_summary: DocumentFeedbackSummary | None


class ConversationDataPointWithDetail(DataPointWithDetail):
    id: Id
    turn_id: ConversationTurnId
