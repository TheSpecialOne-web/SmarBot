from pydantic import BaseModel, Field

from .id import Id, create_id


class WorkflowThreadFlow(BaseModel):
    id: Id


class WorkflowThreadFlowForCreate(BaseModel):
    id: Id = Field(default_factory=create_id)
