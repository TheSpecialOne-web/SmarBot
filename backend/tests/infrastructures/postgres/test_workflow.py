from uuid import uuid4

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models.group import Id as GroupId
from api.domain.models.tenant import Id as TenantId
from api.domain.models.workflow import (
    Description,
    Id as WorkflowId,
    Name,
    WorkflowConfig,
    WorkflowConfigList,
    WorkflowForCreate,
    WorkflowType,
    WorkflowTypeEnum,
)
from api.infrastructures.postgres.models.workflow import Workflow
from api.infrastructures.postgres.workflow import WorkflowRepository
from api.libs.exceptions import NotFound
from tests.conftest import WorkflowListSeed, WorkflowSeed


class TestWorkflowRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.workflow_repo = WorkflowRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self):
        # Input
        group_id = GroupId(value=1)
        workflow_for_create = WorkflowForCreate(
            name=Name(root="test_create_workflow_name"),
            description=Description(root="test_create_workflow_description"),
            type=WorkflowType(root=WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS),
            configs=WorkflowConfigList(
                items=[
                    WorkflowConfig(key="test_key", value="test_value"),
                    WorkflowConfig(key="test_key2", value="test_value2"),
                    WorkflowConfig(key="test_key3", value="test_value3"),
                ]
            ),
        )

        # Execute
        self.workflow_repo.create(group_id, workflow_for_create)

        # データベースの検証
        workflow = self.session.execute(
            select(Workflow).where(
                Workflow.group_id == group_id.value,
                Workflow.id == workflow_for_create.id.root,
            )
        ).scalar_one()

        assert workflow is not None
        assert workflow.name == workflow_for_create.name.root
        assert workflow.description == workflow_for_create.description.root

        # 入力側をdict化
        input_config_dict = {wf_conf.key: wf_conf.value for wf_conf in workflow_for_create.configs.items}
        # データベースから取得したworkflow.configもdict前提で比較
        for key, value in input_config_dict.items():
            assert key in workflow.config, f"DBに '{key}' が存在しません"
            assert (
                workflow.config[key] == value
            ), f"キー '{key}' の値が不一致です (DB: {workflow.config[key]} / Input: {value})"

        # データベースから削除
        self.session.delete(workflow)
        self.session.commit()

    def test_find_by_id(self, workflow_seed: WorkflowSeed):
        # Input
        workflow, _ = workflow_seed

        # Execute
        found_workflow = self.workflow_repo.find_by_id(workflow.id)

        assert found_workflow is not None
        assert found_workflow.id == workflow.id
        assert found_workflow.name == workflow.name
        assert found_workflow.description == workflow.description
        assert found_workflow.type == workflow.type

    def test_find_by_id_not_found(self):
        # Input
        workflow_id = WorkflowId(root=uuid4())

        # Execute
        with pytest.raises(NotFound):
            self.workflow_repo.find_by_id(workflow_id)

    def test_find_by_id_and_tenant_id(self, workflow_seed: WorkflowSeed):
        # Input
        workflow, tenant = workflow_seed
        workflow_id = workflow.id
        tenant_id = tenant.id

        # Execute
        found_workflow = self.workflow_repo.find_with_group_by_id_and_tenant_id(tenant_id, workflow_id)

        assert found_workflow is not None
        assert found_workflow.id == workflow.id
        assert found_workflow.name == workflow.name
        assert found_workflow.description == workflow.description
        assert found_workflow.type == workflow.type

    def test_find_by_id_and_tenant_id_not_found(self, workflow_seed: WorkflowSeed):
        # Input
        workflow, tenant = workflow_seed
        workflow_id = workflow.id
        tenant_id = TenantId(value=tenant.id.value + 1)

        # Execute
        with pytest.raises(NotFound):
            self.workflow_repo.find_with_group_by_id_and_tenant_id(tenant_id, workflow_id)

    def test_find_by_tenant_id(self, workflow_list_seed: WorkflowListSeed):
        # Input
        workflow_list, group, tenant = workflow_list_seed
        tenant_id = tenant.id

        # Execute
        found_workflows = self.workflow_repo.find_by_tenant_id(tenant_id)

        assert len(found_workflows) == len(workflow_list)
        assert found_workflows == workflow_list

    def test_find_by_tenant_id_and_group_ids(self, workflow_list_seed: WorkflowListSeed):
        workflow_list, group, tenant = workflow_list_seed
        tenant_id = tenant.id

        # Execute
        found_workflows = self.workflow_repo.find_by_tenant_id_and_group_ids(tenant_id, [group.id])
        assert found_workflows == workflow_list
