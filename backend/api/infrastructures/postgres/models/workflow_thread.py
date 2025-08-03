from typing import TYPE_CHECKING
import uuid

from sqlalchemy import UUID, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import workflow_thread as wf_thread_domain
from api.domain.models.user import Id as UserId
from api.domain.models.workflow import Id as WorkflowId

from .base import BaseModel

if TYPE_CHECKING:
    from .workflow import Workflow
    from .workflow_thread_flow import WorkflowThreadFlow


class WorkflowThread(BaseModel):
    __tablename__ = "workflow_threads"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="workflow_threads",
    )

    workflow_thread_flows: Mapped[list["WorkflowThreadFlow"]] = relationship(
        "WorkflowThreadFlow",
        back_populates="workflow_thread",
    )

    @classmethod
    def from_create_domain(
        cls,
        workflow_id: WorkflowId,
        user_id: UserId,
        wf_thread_for_create: wf_thread_domain.WorkflowThreadForCreate,
    ) -> "WorkflowThread":
        return cls(
            id=wf_thread_for_create.id.root,
            title=wf_thread_for_create.title.root,
            user_id=user_id.value,
            workflow_id=workflow_id.root,
        )

    def to_domain(self) -> wf_thread_domain.WorkflowThread:
        return wf_thread_domain.WorkflowThread(
            id=wf_thread_domain.Id(root=self.id),
            title=wf_thread_domain.Title(root=self.title),
        )
