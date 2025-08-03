from pydantic import BaseModel

from ..bot import (
    Id as BotId,
    Name,
)
from .meter import PDFParserCountType, Quantity


class BotPdfParserPageCount(BaseModel):
    bot_id: BotId
    bot_name: Name
    page_count: Quantity
    count_type: PDFParserCountType
