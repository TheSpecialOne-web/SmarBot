from abc import ABC, abstractmethod
from datetime import datetime

from ..tenant import Id as TenantId
from ..token import TokenCount
from ..user import Id as UserId
from ..workflow import Id as WorkflowId
from .workflow_thread import (
    Id as WorkflowThreadId,
    WorkflowThread,
    WorkflowThreadForCreate,
)
from .workflow_thread_flow import (
    Id as WorkflowThreadFlowId,
    WorkflowThreadFlow,
    WorkflowThreadFlowForCreate,
)
from .workflow_thread_flow_step import (
    WorkflowThreadFlowStep,
    WorkflowThreadFlowStepForCreate,
)


class IWorkflowThreadRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: WorkflowThreadId) -> WorkflowThread:
        pass

    @abstractmethod
    def find_flow_by_id_and_thread_id(
        self, wf_thread_id: WorkflowThreadId, id: WorkflowThreadFlowId
    ) -> WorkflowThreadFlow:
        pass

    @abstractmethod
    def find_active_wf_thread_flow_step_by_wf_thread_flow_id(
        self, wf_thread_flow_id: WorkflowThreadFlowId
    ) -> list[WorkflowThreadFlowStep]:
        pass

    @abstractmethod
    def create(
        self, workflow_id: WorkflowId, user_id: UserId, wf_thread_for_create: WorkflowThreadForCreate
    ) -> WorkflowThread:
        pass

    @abstractmethod
    def create_flow(
        self, wf_thread_id: WorkflowThreadId, wf_thread_flow_for_create: WorkflowThreadFlowForCreate
    ) -> WorkflowThreadFlow:
        pass

    @abstractmethod
    def create_flow_step(
        self,
        wf_thread_flow_id: WorkflowThreadFlowId,
        wf_thread_flow_step_for_create: WorkflowThreadFlowStepForCreate,
    ) -> WorkflowThreadFlowStep:
        pass

    @abstractmethod
    def bulk_update_wf_thread_flow_step(self, wf_thread_flow_steps: list[WorkflowThreadFlowStep]):
        pass

    @abstractmethod
    def get_workflow_thread_token_count_by_tenant_id(
        self, tenant_id: TenantId, start_date_time: datetime, end_date_time: datetime
    ) -> TokenCount:
        pass
