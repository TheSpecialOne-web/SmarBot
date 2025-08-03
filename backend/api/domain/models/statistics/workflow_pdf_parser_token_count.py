from pydantic import BaseModel

from ..token import TokenCount
from ..workflow import Id, Name


class WorkflowPdfParserTokenCount(BaseModel):
    workflow_id: Id
    workflow_name: Name
    token_count: TokenCount
