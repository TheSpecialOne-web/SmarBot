from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import UUID, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import workflow as workflow_domain
from api.domain.models.group import Id as GroupId
from api.domain.models.workflow.type import WorkflowTypeEnum
from api.domain.models.workflow.ursa.generate_construction_specifications.generate_construction_specifications import (
    GenerateConstructionSpecificationsWorkflow,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .group import Group
    from .metering import Metering
    from .workflow_thread import WorkflowThread


class Workflow(BaseModel):
    __tablename__ = "workflows"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id", onupdate="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")

    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="workflows",
    )

    workflow_threads: Mapped[list["WorkflowThread"]] = relationship(
        "WorkflowThread",
        back_populates="workflow",
    )

    meterings: Mapped[list["Metering"]] = relationship(
        "Metering",
        back_populates="workflow",
    )

    @classmethod
    def from_create(cls, group_id: GroupId, wfc: workflow_domain.WorkflowForCreate) -> "Workflow":
        # config を辞書形式に変換
        config_dict = {item.key: item.value for item in wfc.configs.items}
        return cls(
            id=wfc.id.root,
            group_id=group_id.value,
            name=wfc.name.root,
            type=wfc.type.to_str(),
            description=wfc.description.root,
            config=config_dict,
        )

    def to_domain(self) -> workflow_domain.Workflow:
        workflow = workflow_domain.Workflow(
            id=workflow_domain.Id(root=self.id),
            name=workflow_domain.Name(root=self.name),
            type=workflow_domain.WorkflowType.from_str(self.type),
            description=workflow_domain.Description(root=self.description),
            configs=workflow_domain.WorkflowConfigList(
                items=[
                    workflow_domain.WorkflowConfig(
                        key=key,
                        value=value,
                    )
                    for key, value in self.config.items()
                ]
            ),
        )
        match self.type:
            case WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS:
                return GenerateConstructionSpecificationsWorkflow(
                    **workflow.model_dump(),
                )
            case _:
                raise ValueError(f"Unsupported workflow type: {self.type}")

    def to_domain_with_group(self) -> workflow_domain.WorkflowWithGroup:
        workflow = self.to_domain()
        return workflow_domain.WorkflowWithGroup(
            id=workflow.id,
            name=workflow.name,
            type=workflow.type,
            description=workflow.description,
            configs=workflow.configs,
            group=self.group.to_domain(),
        )
