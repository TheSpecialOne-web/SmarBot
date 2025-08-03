from datetime import datetime
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

from api.domain.models import bot as bot_domain
from api.domain.models.group import Id as GroupId
from api.domain.models.llm.model import ModelFamily
from api.domain.models.llm.pdf_parser import PdfParser
from api.domain.models.token import TokenCount
from api.domain.models.workflow import (
    Description,
    Id as WorkflowId,
    Name,
    RunParameter,
    RunStepParams,
    WorkflowConfig,
    WorkflowConfigList,
    WorkflowForCreate,
    WorkflowType,
    WorkflowTypeEnum,
)
from api.domain.models.workflow.ursa import generate_construction_specifications as gcs_domain
from api.usecase.workflows import (
    CreateWorkflowInput,
    DIOcrPageCount,
    LLMOcrPageCount,
    RunWorkflowInput,
    RunWorkflowItem,
    RunWorkflowOutput,
    UseBatchProcessing,
)
from api.usecase.workflows.ursa.generate_construction_specifications import (
    GenerateConstructionSpecificationsWorkflowUseCase,
)


def dummy_bot() -> bot_domain.Bot:
    return bot_domain.Bot(
        id=bot_domain.Id(value=1),
        name=bot_domain.Name(value="test_bot_name"),
        description=bot_domain.Description(value="テスト用ボット"),
        group_id=GroupId(value=1),
        index_name=None,
        container_name=None,
        approach=bot_domain.Approach.NEOLLM,
        pdf_parser=PdfParser.PYPDF,
        example_questions=[],
        search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
        response_generator_model_family=ModelFamily.GPT_35_TURBO,
        image_generator_model_family=None,
        approach_variables=[],
        enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
        enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
        icon_url=None,
        icon_color=bot_domain.IconColor(root="#AA68FF"),
        max_conversation_turns=None,
        created_at=bot_domain.CreatedAt(root=datetime.now()),
        status=bot_domain.Status.ACTIVE,
        endpoint_id=bot_domain.EndpointId(root=uuid4()),
    )


class TestGenerateConstructionSpecificationsUsecase:
    @pytest.fixture
    def setup(self):
        self.bot_repo = Mock()
        self.workflow_repo = Mock()
        self.workflow_usecase = GenerateConstructionSpecificationsWorkflowUseCase(
            bot_repo=self.bot_repo,
            workflow_repo=self.workflow_repo,
        )

    def test_create(self, setup):
        # Input
        group_id = GroupId(value=1)
        input = CreateWorkflowInput(
            name=Name(root="test_workflow_name"),
            description=Description(root="test_workflow_description"),
            type=WorkflowType(root=WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS),
            configs=WorkflowConfigList(items=[WorkflowConfig(key="bot_id", value=1)]),
        )

        # mock
        bot = dummy_bot()
        self.workflow_usecase.bot_repo.find_by_id_and_group_id.return_value = bot
        fixed_uuid = "123e4567-e89b-12d3-a456-426614174000"

        with patch("api.domain.models.workflow.id.uuid4", return_value=UUID(fixed_uuid)):
            wfc = WorkflowForCreate(
                name=input.name,
                description=input.description,
                type=input.type,
                configs=WorkflowConfigList(
                    items=[
                        WorkflowConfig(key="bot_id", value=bot.id.value),
                    ],
                ),
            )

            # Execute
            self.workflow_usecase.create(group_id=group_id, input=input)

        # Assert
        self.workflow_usecase.workflow_repo.create.assert_called_once_with(
            group_id=group_id,
            wfc=wfc,
        )

    def test_run_step_1(self, setup):
        # Input
        input = RunWorkflowInput(
            step=1,
            params=RunStepParams(
                items=[RunParameter(key="test", value="test")],
            ),
        )

        # mock
        workflow = gcs_domain.GenerateConstructionSpecificationsWorkflow(
            id=WorkflowId(root=uuid4()),
            name=Name(root="test_workflow_name"),
            description=Description(root="test_workflow_description"),
            type=WorkflowType(root=WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS),
            configs=WorkflowConfigList(items=[WorkflowConfig(key="bot_id", value=1)]),
        )

        # Execute
        output = self.workflow_usecase.run(input=input, workflow=workflow)

        # Assert
        assert output == RunWorkflowOutput(
            items=[RunWorkflowItem(key="test", value="test")],
            token_count=TokenCount(root=100),
            di_ocr_page_count=DIOcrPageCount(root=12),
            llm_ocr_page_count=LLMOcrPageCount(root=30),
            use_batch_processing=UseBatchProcessing(root=True),
        )

    def test_run_step_2(self, setup):
        # Input
        input = RunWorkflowInput(
            step=2,
            params=RunStepParams(items=[]),
        )

        # mock
        workflow = gcs_domain.GenerateConstructionSpecificationsWorkflow(
            id=WorkflowId(root=uuid4()),
            name=Name(root="test_workflow_name"),
            description=Description(root="test_workflow_description"),
            type=WorkflowType(root=WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS),
            configs=WorkflowConfigList(items=[WorkflowConfig(key="bot_id", value=1)]),
        )

        # Execute
        output = self.workflow_usecase.run(input=input, workflow=workflow)

        # Assert
        assert output == RunWorkflowOutput(
            items=[RunWorkflowItem(key="test", value="test")],
            token_count=TokenCount(root=100),
            di_ocr_page_count=DIOcrPageCount(root=12),
            llm_ocr_page_count=LLMOcrPageCount(root=30),
            use_batch_processing=UseBatchProcessing(root=True),
        )
