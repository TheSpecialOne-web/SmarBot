from typing import TYPE_CHECKING
import uuid

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import workflow_thread as wf_thread_domain
from api.domain.models.workflow_thread import workflow_thread_flow as wf_thread_flow_domain

from .base import BaseModel

if TYPE_CHECKING:
    from .workflow_thread import WorkflowThread
    from .workflow_thread_flow_step import WorkflowThreadFlowStep


class WorkflowThreadFlow(BaseModel):
    __tablename__ = "workflow_thread_flows"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    workflow_thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_threads.id"), nullable=False
    )
    workflow_thread: Mapped["WorkflowThread"] = relationship(
        "WorkflowThread",
        back_populates="workflow_thread_flows",
    )
    workflow_thread_flow_steps: Mapped[list["WorkflowThreadFlowStep"]] = relationship(
        "WorkflowThreadFlowStep",
        back_populates="workflow_thread_flow",
    )

    @classmethod
    def from_create_domain(
        cls,
        wf_thread_id: wf_thread_domain.Id,
        flow_for_create: wf_thread_flow_domain.WorkflowThreadFlowForCreate,
    ) -> "WorkflowThreadFlow":
        return cls(
            id=flow_for_create.id.root,
            workflow_thread_id=wf_thread_id.root,
        )

    def to_domain(self) -> wf_thread_flow_domain.WorkflowThreadFlow:
        return wf_thread_flow_domain.WorkflowThreadFlow(
            id=wf_thread_flow_domain.Id(root=self.id),
        )
