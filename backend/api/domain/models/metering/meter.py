from pydantic import BaseModel

from ..bot import Id as BotId
from ..tenant import Id as TenantId
from ..workflow import Id as WorkflowId
from .quantity import Quantity
from .type import PDFParserCountType, Type


class MeterProps(BaseModel):
    tenant_id: TenantId
    bot_id: BotId | None = None
    workflow_id: WorkflowId | None = None
    quantity: Quantity


class Meter(MeterProps):
    type: Type


class PdfParserMeterForCreate(MeterProps):
    type: PDFParserCountType
