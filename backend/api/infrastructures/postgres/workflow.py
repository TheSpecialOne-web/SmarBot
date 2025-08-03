from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.domain.models import workflow as workflow_domain
from api.domain.models.group import Id as GroupId
from api.domain.models.tenant import Id as TenantId
from api.libs.exceptions import NotFound

from .models.group import Group
from .models.workflow import Workflow


class WorkflowRepository(workflow_domain.IWorkflowRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, group_id: GroupId, wfc: workflow_domain.WorkflowForCreate) -> None:
        try:
            workflow = Workflow.from_create(group_id=group_id, wfc=wfc)
            self.session.add(workflow)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_by_id(self, id: workflow_domain.Id) -> workflow_domain.Workflow:
        workflow = self.session.execute(select(Workflow).where(Workflow.id == id.root)).scalar_one_or_none()
        if workflow is None:
            raise NotFound("Workflow not found")
        return workflow.to_domain()

    def find_with_group_by_id_and_tenant_id(
        self, tenant_id: TenantId, id: workflow_domain.Id
    ) -> workflow_domain.WorkflowWithGroup:
        workflow = self.session.execute(
            select(Workflow)
            .join(Group, Group.id == Workflow.group_id)
            .where(Group.tenant_id == tenant_id.value)
            .where(Workflow.id == id.root)
            .options(joinedload(Workflow.group))
        ).scalar_one_or_none()
        if workflow is None:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")
        return workflow.to_domain_with_group()

    def find_by_tenant_id(self, tenant_id: TenantId) -> list[workflow_domain.Workflow]:
        workflows = (
            self.session.execute(select(Workflow).join(Group).where(Group.tenant_id == tenant_id.value))
            .scalars()
            .all()
        )
        return [workflow.to_domain() for workflow in workflows]

    def find_by_tenant_id_and_group_ids(
        self, tenant_id: TenantId, group_ids: list[GroupId]
    ) -> list[workflow_domain.Workflow]:
        group_ids_values = [group_id.value for group_id in group_ids]
        workflows = (
            self.session.execute(
                select(Workflow)
                .where(Workflow.group_id.in_(group_ids_values))
                .where(Group.tenant_id == tenant_id.value)
            )
            .scalars()
            .all()
        )
        return [workflow.to_domain() for workflow in workflows]
