from datetime import datetime, timedelta

from api.database import SessionFactory
from api.domain.models import workflow_thread as wf_thread_domain
from api.domain.models.token import TokenCount
from api.domain.models.workflow_thread import (
    workflow_thread_flow as wf_thread_flow_domain,
    workflow_thread_flow_step as wf_thread_flow_step_domain,
)
from api.infrastructures.postgres.workflow_thread import WorkflowThreadRepository
from tests.conftest import (
    UserSeed,
    WorkflowSeed,
    WorkflowThreadFlowSeed,
    WorkflowThreadFlowStepSeed,
    WorkflowThreadSeed,
)


class TestWorkflowThreadRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.workflow_thread_repo = WorkflowThreadRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self, workflow_seed: WorkflowSeed, user_seed: UserSeed):
        # Input
        user_id, _, _, _, _ = user_seed
        workflow, _ = workflow_seed
        wf_thread_for_create = wf_thread_domain.WorkflowThreadForCreate(
            title=wf_thread_domain.Title(root="test_create_workflow_thread_title"),
        )

        # Execute
        result = self.workflow_thread_repo.create(workflow.id, user_id, wf_thread_for_create)

        # データベースの検証
        assert result is not None
        assert result.id == wf_thread_for_create.id
        assert result.title == wf_thread_for_create.title

    def test_create_flow(self, workflow_thread_seed: WorkflowThreadSeed):
        # Input
        _, _, wf_thread = workflow_thread_seed
        wf_thread_flow_for_create = wf_thread_flow_domain.WorkflowThreadFlowForCreate()

        # Execute
        result = self.workflow_thread_repo.create_flow(wf_thread.id, wf_thread_flow_for_create)

        assert result is not None
        assert result.id == wf_thread_flow_for_create.id

    def test_create_flow_step(self, workflow_thread_flow_seed: WorkflowThreadFlowSeed):
        # Input
        _, _, _, wf_thread_flow = workflow_thread_flow_seed
        wf_thread_flow_step_for_create = wf_thread_flow_step_domain.WorkflowThreadFlowStepForCreate(
            step=wf_thread_flow_step_domain.Step(root=1),
            input=wf_thread_flow_step_domain.Input(
                items=[wf_thread_flow_step_domain.InputItem(key="test_key", value="test_value")]
            ),
            output=wf_thread_flow_step_domain.Output(
                items=[wf_thread_flow_step_domain.OutputItem(key="test_key", value="test_value")]
            ),
            is_active=wf_thread_flow_step_domain.IsActive(root=True),
            status=wf_thread_flow_step_domain.Status.PROCESSING,
            token_count=TokenCount(root=100),
        )

        # Execute
        result = self.workflow_thread_repo.create_flow_step(
            wf_thread_flow_id=wf_thread_flow.id,
            wf_thread_flow_step_for_create=wf_thread_flow_step_for_create,
        )

        # データベースの検証
        assert result is not None
        assert result.id == wf_thread_flow_step_for_create.id
        assert result.step == wf_thread_flow_step_for_create.step
        assert result.input == wf_thread_flow_step_for_create.input
        assert result.output == wf_thread_flow_step_for_create.output
        assert result.is_active == wf_thread_flow_step_for_create.is_active
        assert result.status == wf_thread_flow_step_for_create.status
        assert result.token_count == wf_thread_flow_step_for_create.token_count

    def test_find_by_id(self, workflow_thread_seed: WorkflowThreadSeed):
        # Input
        _, _, wf_thread = workflow_thread_seed

        # Execute
        result = self.workflow_thread_repo.find_by_id(wf_thread.id)

        # データベースの検証
        assert result is not None
        assert result.id == wf_thread.id
        assert result.title == wf_thread.title

    def test_find_flow_by_id_and_thread_id(self, workflow_thread_flow_seed: WorkflowThreadFlowSeed):
        # Input
        _, _, wf_thread_id, wf_thread_flow = workflow_thread_flow_seed

        # Execute
        result = self.workflow_thread_repo.find_flow_by_id_and_thread_id(wf_thread_id, wf_thread_flow.id)

        # データベースの検証
        assert result is not None
        assert result.id == wf_thread_flow.id

    def test_get_workflow_thread_token_count_by_tenant_id(
        self, workflow_thread_flow_step_seed: WorkflowThreadFlowStepSeed
    ):
        # Input
        tenant_id, _, _, _, wf_thread_flow_step = workflow_thread_flow_step_seed
        start_date_time = datetime.now() - timedelta(days=2)
        end_date_time = start_date_time + timedelta(days=2)

        want = TokenCount(root=wf_thread_flow_step.token_count.root)

        # Execute
        got = self.workflow_thread_repo.get_workflow_thread_token_count_by_tenant_id(
            tenant_id, start_date_time, end_date_time
        )

        # データベースの検証
        assert got == want
