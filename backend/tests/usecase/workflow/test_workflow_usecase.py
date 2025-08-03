from unittest.mock import Mock
import uuid

import pytest

from api.domain.models.tenant import Id as TenantId
from api.domain.models.workflow import (
    Description,
    Id,
    Name,
    Workflow,
    WorkflowConfigList,
    WorkflowType,
    WorkflowTypeEnum,
)
from api.domain.models.workflow.specifications import WorkflowConfigFieldType
from api.usecase.workflows.workflow import WorkflowUseCase


class TestWorkflowUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo = Mock()
        self.group_repo = Mock()
        self.workflow_repo = Mock()
        self.workflow_thread_repo = Mock()
        self.metering_repo = Mock()
        self.bot_repo = Mock()
        self.workflow_usecase = WorkflowUseCase(
            tenant_repo=self.tenant_repo,
            group_repo=self.group_repo,
            workflow_repo=self.workflow_repo,
            workflow_thread_repo=self.workflow_thread_repo,
            metering_repo=self.metering_repo,
            bot_repo=self.bot_repo,
        )

    def test_get_workflow_parameters_for_create_by_type(self, setup):
        # Input
        workflow_type = WorkflowType(root=WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS)
        workflow_parameters = self.workflow_usecase.get_workflow_parameters_for_create_by_type(workflow_type)
        assert len(workflow_parameters) == 1
        assert workflow_parameters[0].key == "bot_id"
        assert workflow_parameters[0].display_name == "アシスタント"
        assert workflow_parameters[0].description == "アシスタントを選択してください"
        assert workflow_parameters[0].type == WorkflowConfigFieldType.BOT_ID
        assert workflow_parameters[0].required is True
        assert workflow_parameters[0].default_value is None

    def test_get_workflows(self, setup):
        # Input
        tenant_id = TenantId(value=1)
        want = [
            Workflow(
                id=Id(root=uuid.uuid4()),
                name=Name(root="test_name"),
                description=Description(root="test_description"),
                type=WorkflowType(root=WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS),
                configs=WorkflowConfigList(items=[]),
            )
            for _ in range(3)
        ]

        self.workflow_usecase.workflow_repo.find_by_tenant_id.return_value = want

        # Execute
        found_workflows = self.workflow_usecase.get_workflows_by_tenant_id(tenant_id)
        assert found_workflows == want
