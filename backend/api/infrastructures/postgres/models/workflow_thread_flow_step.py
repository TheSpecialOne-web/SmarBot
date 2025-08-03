from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import UUID, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models.token import TokenCount
from api.domain.models.workflow_thread import (
    workflow_thread_flow as wf_thread_flow_domain,
    workflow_thread_flow_step as wf_thread_flow_step_domain,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .workflow_thread_flow import WorkflowThreadFlow


class WorkflowThreadFlowStep(BaseModel):
    __tablename__ = "workflow_thread_flow_steps"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    workflow_thread_flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_thread_flows.id"), nullable=False
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="processing")
    token_count: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    workflow_thread_flow: Mapped["WorkflowThreadFlow"] = relationship(
        "WorkflowThreadFlow",
        back_populates="workflow_thread_flow_steps",
    )

    @classmethod
    def from_create_domain(
        cls,
        wf_thread_flow_id: wf_thread_flow_domain.Id,
        wf_thread_flow_step_for_create: wf_thread_flow_step_domain.WorkflowThreadFlowStepForCreate,
    ) -> "WorkflowThreadFlowStep":
        input_dict = {item.key: item.value for item in wf_thread_flow_step_for_create.input.items}
        output_dict = {item.key: item.value for item in wf_thread_flow_step_for_create.output.items}
        return cls(
            id=wf_thread_flow_step_for_create.id.root,
            workflow_thread_flow_id=wf_thread_flow_id.root,
            step=wf_thread_flow_step_for_create.step.root,
            input=input_dict,
            output=output_dict,
            token_count=wf_thread_flow_step_for_create.token_count.root,
        )

    def to_domain(self) -> wf_thread_flow_step_domain.WorkflowThreadFlowStep:
        return wf_thread_flow_step_domain.WorkflowThreadFlowStep(
            id=wf_thread_flow_step_domain.Id(root=self.id),
            step=wf_thread_flow_step_domain.Step(root=self.step),
            input=wf_thread_flow_step_domain.Input(
                items=[wf_thread_flow_step_domain.InputItem(key=key, value=value) for key, value in self.input.items()]
            ),
            output=wf_thread_flow_step_domain.Output(
                items=[
                    wf_thread_flow_step_domain.OutputItem(key=key, value=value) for key, value in self.output.items()
                ]
            ),
            is_active=wf_thread_flow_step_domain.IsActive(root=self.is_active),
            status=wf_thread_flow_step_domain.Status(self.status),
            token_count=TokenCount(root=self.token_count),
        )
