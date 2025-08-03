from api.domain.models import (
    bot as bot_domain,
    workflow as workflow_domain,
)
from api.domain.models.bot import Id as BotId
from api.domain.models.group import Id as GroupId
from api.domain.models.token import TokenCount
from api.domain.models.workflow.ursa.generate_construction_specifications import (
    GenerateConstructionSpecificationsWorkflow,
)
from api.usecase.workflows import (
    CreateWorkflowInput,
    DIOcrPageCount,
    LLMOcrPageCount,
    RunWorkflowInput,
    RunWorkflowItem,
    RunWorkflowOutput,
    UseBatchProcessing,
)

from .. import ISpecificWorkflowUseCaseBase


class GenerateConstructionSpecificationsWorkflowUseCase(
    ISpecificWorkflowUseCaseBase[GenerateConstructionSpecificationsWorkflow],
):
    def __init__(self, bot_repo: bot_domain.IBotRepository, workflow_repo: workflow_domain.IWorkflowRepository):
        self.bot_repo = bot_repo
        self.workflow_repo = workflow_repo

    def create(self, group_id: GroupId, input: CreateWorkflowInput) -> None:
        # ワークフローの作成
        bot_id = BotId(value=input.configs.get_value("bot_id"))
        bot = self.bot_repo.find_by_id_and_group_id(id=bot_id, group_id=group_id)

        wfc = workflow_domain.WorkflowForCreate(
            name=input.name,
            description=input.description,
            type=input.type,
            configs=workflow_domain.WorkflowConfigList(
                items=[
                    workflow_domain.WorkflowConfig(
                        key="bot_id",
                        value=bot.id.value,
                    ),
                ],
            ),
        )
        self.workflow_repo.create(group_id=group_id, wfc=wfc)

    def run(self, input: RunWorkflowInput, workflow: GenerateConstructionSpecificationsWorkflow) -> RunWorkflowOutput:
        # TODO：URSAの人に書いてもらう部分
        print("run")
        print(input)
        print(workflow)
        return RunWorkflowOutput(
            items=[RunWorkflowItem(key="test", value="test")],
            token_count=TokenCount(root=100),
            di_ocr_page_count=DIOcrPageCount(root=12),
            llm_ocr_page_count=LLMOcrPageCount(root=30),
            use_batch_processing=UseBatchProcessing(root=True),
        )
