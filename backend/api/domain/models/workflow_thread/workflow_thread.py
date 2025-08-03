from pydantic import BaseModel, Field

from .id import Id, create_id
from .title import Title


class WorkflowThreadProps(BaseModel):
    title: Title


class WorkflowThreadForCreate(WorkflowThreadProps):
    id: Id = Field(default_factory=create_id)


class WorkflowThread(WorkflowThreadProps):
    id: Id
