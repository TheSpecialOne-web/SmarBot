from pydantic import Field

from ...data_point import DataPoint
from .id import Id, create_id


class ChatCompletionDataPoint(DataPoint):
    id: Id = Field(default_factory=create_id)
