from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from api.domain.models import workflow_thread as wf_thread_domain
from api.domain.models.tenant import Id as TenantId
from api.domain.models.token import TokenCount
from api.domain.models.user import Id as UserId
from api.domain.models.workflow import Id as WorkflowId
from api.domain.models.workflow_thread import (
    workflow_thread_flow as wf_thread_flow_domain,
    workflow_thread_flow_step as wf_thread_flow_step_domain,
)
from api.libs.exceptions import NotFound

from .models.group import Group
from .models.workflow import Workflow
from .models.workflow_thread import WorkflowThread
from .models.workflow_thread_flow import WorkflowThreadFlow
from .models.workflow_thread_flow_step import WorkflowThreadFlowStep


class WorkflowThreadRepository(wf_thread_domain.IWorkflowThreadRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, id: wf_thread_domain.Id) -> wf_thread_domain.WorkflowThread:
        wf_thread = self.session.execute(select(WorkflowThread).filter(WorkflowThread.id == id.root)).scalars().first()
        if not wf_thread:
            raise NotFound("ワークフロースレッドが見つかりませんでした。")
        return wf_thread.to_domain()

    def find_flow_by_id_and_thread_id(
        self,
        wf_thread_id: wf_thread_domain.Id,
        id: wf_thread_flow_domain.Id,
    ) -> wf_thread_flow_domain.WorkflowThreadFlow:
        wf_thread_flow = (
            self.session.execute(
                select(WorkflowThreadFlow).filter(
                    WorkflowThreadFlow.id == id.root, WorkflowThreadFlow.workflow_thread_id == wf_thread_id.root
                )
            )
            .scalars()
            .first()
        )
        if not wf_thread_flow:
            raise NotFound("ワークフロースレッドフローが見つかりませんでした。")
        return wf_thread_flow.to_domain()

    def find_active_wf_thread_flow_step_by_wf_thread_flow_id(
        self, wf_thread_flow_id: wf_thread_flow_domain.Id
    ) -> list[wf_thread_flow_step_domain.WorkflowThreadFlowStep]:
        wf_thread_flow_steps = (
            self.session.execute(
                select(WorkflowThreadFlowStep).filter(
                    WorkflowThreadFlowStep.workflow_thread_flow_id == wf_thread_flow_id.root
                )
            )
            .scalars()
            .all()
        )
        return [wf_thread_flow_step.to_domain() for wf_thread_flow_step in wf_thread_flow_steps]

    def create(
        self, workflow_id: WorkflowId, user_id: UserId, wf_thread_for_create: wf_thread_domain.WorkflowThreadForCreate
    ) -> wf_thread_domain.WorkflowThread:
        try:
            new_wf_thread = WorkflowThread.from_create_domain(
                workflow_id=workflow_id,
                user_id=user_id,
                wf_thread_for_create=wf_thread_for_create,
            )
            self.session.add(new_wf_thread)
            self.session.commit()
            return new_wf_thread.to_domain()
        except Exception as e:
            self.session.rollback()
            raise e

    def create_flow(
        self,
        wf_thread_id: wf_thread_domain.Id,
        wf_thread_flow_for_create: wf_thread_flow_domain.WorkflowThreadFlowForCreate,
    ) -> wf_thread_flow_domain.WorkflowThreadFlow:
        try:
            new_wf_thread_flow = WorkflowThreadFlow.from_create_domain(
                wf_thread_id=wf_thread_id,
                flow_for_create=wf_thread_flow_for_create,
            )
            self.session.add(new_wf_thread_flow)
            self.session.commit()
            return new_wf_thread_flow.to_domain()
        except Exception as e:
            self.session.rollback()
            raise e

    def create_flow_step(
        self,
        wf_thread_flow_id: wf_thread_flow_domain.Id,
        wf_thread_flow_step_for_create: wf_thread_flow_step_domain.WorkflowThreadFlowStepForCreate,
    ) -> wf_thread_flow_step_domain.WorkflowThreadFlowStep:
        try:
            new_wf_thread_flow_step = WorkflowThreadFlowStep.from_create_domain(
                wf_thread_flow_id=wf_thread_flow_id,
                wf_thread_flow_step_for_create=wf_thread_flow_step_for_create,
            )
            self.session.add(new_wf_thread_flow_step)
            self.session.commit()
            return new_wf_thread_flow_step.to_domain()
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_update_wf_thread_flow_step(
        self, wf_thread_flow_steps: list[wf_thread_flow_step_domain.WorkflowThreadFlowStep]
    ):
        for wf_thread_flow_step in wf_thread_flow_steps:
            self.session.execute(
                update(WorkflowThreadFlowStep)
                .where(WorkflowThreadFlowStep.id == wf_thread_flow_step.id.root)
                .values(
                    is_active=wf_thread_flow_step.is_active.root,
                )
            )
        self.session.commit()

    def get_workflow_thread_token_count_by_tenant_id(
        self, tenant_id: TenantId, start_date_time: datetime, end_date_time: datetime
    ) -> TokenCount:
        stmt = (
            select(func.coalesce(func.sum(WorkflowThreadFlowStep.token_count), 0))
            .select_from(WorkflowThreadFlowStep)
            .join(WorkflowThreadFlow, WorkflowThreadFlow.id == WorkflowThreadFlowStep.workflow_thread_flow_id)
            .join(WorkflowThread, WorkflowThread.id == WorkflowThreadFlow.workflow_thread_id)
            .join(Workflow, Workflow.id == WorkflowThread.workflow_id)
            .join(Group, Group.id == Workflow.group_id)
            .where(Group.tenant_id == tenant_id.value)
            .where(WorkflowThreadFlowStep.created_at >= start_date_time)
            .where(WorkflowThreadFlowStep.created_at < end_date_time)
            .execution_options(include_deleted=True)
        )
        return TokenCount(root=self.session.execute(stmt).scalar_one())
