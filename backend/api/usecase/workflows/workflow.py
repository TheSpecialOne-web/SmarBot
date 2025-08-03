from abc import ABC, abstractmethod
from typing import Any

from injector import inject
from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    metering as metering_domain,
    tenant as tenant_domain,
    workflow as workflow_domain,
    workflow_thread as wf_thread_domain,
)
from api.domain.models.user import (
    Id as UserId,
    Role,
)
from api.domain.models.workflow import (
    Workflow,
    WorkflowType,
    WorkflowTypeEnum,
)
from api.domain.models.workflow.specifications import (
    ParamSpecForCreate,
    WorkflowSpecForCreateBase,
    WorkflowSpecForRunBase,
)
from api.domain.models.workflow.specifications.workflow_spec_for_run import (
    RunWorkflowStepFields,
)
from api.domain.models.workflow.ursa.generate_construction_specifications import (
    GenerateConstructionSpecificationsWorkflow,
)
from api.domain.models.workflow.ursa.generate_construction_specifications.specifications import (
    GenerateConstructionSpecificationsWorkflowSpecForCreate,
    GenerateConstructionSpecificationsWorkflowSpecForRun,
)
from api.domain.models.workflow_thread import (
    workflow_thread_flow as wf_thread_flow_domain,
    workflow_thread_flow_step as wf_thread_flow_step_domain,
)
from api.libs.exceptions import BadRequest
from api.usecase.workflows.ursa.generate_construction_specifications import (
    GenerateConstructionSpecificationsWorkflowUseCase,
)

from .base import (
    CreateWorkflowInput,
    ISpecificWorkflowUseCaseBase,
    RunWorkflowInput,
    RunWorkflowOutput,
)


class GetCurrentUserWorkflowInput(BaseModel):
    tenant_id: tenant_domain.Id
    user_id: UserId
    roles: list[Role]

    def is_tenant_admin(self) -> bool:
        return Role.ADMIN in self.roles


class GetWorkflowWithRunSchemaOutput(Workflow):
    schemas: list[RunWorkflowStepFields]


class IWorkflowUseCase(ABC):
    @abstractmethod
    def get_workflow_types(self) -> list[WorkflowType]:
        pass

    @abstractmethod
    def get_workflow_parameters_for_create_by_type(self, workflow_type: WorkflowType) -> list[ParamSpecForCreate]:
        pass

    @abstractmethod
    def get_workflows_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[Workflow]:
        pass

    @abstractmethod
    def get_workflows(self, input: GetCurrentUserWorkflowInput) -> list[Workflow]:
        pass

    @abstractmethod
    def create(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        input: CreateWorkflowInput,
    ) -> None:
        pass

    @abstractmethod
    def run(
        self,
        workflow_id: workflow_domain.Id,
        wf_thread_id: wf_thread_domain.Id | None,
        wf_thread_flow_id: wf_thread_flow_domain.Id | None,
        user_id: UserId,
        tenant_id: tenant_domain.Id,
        input: RunWorkflowInput,
    ) -> RunWorkflowOutput:
        pass

    @abstractmethod
    def get_workflow_with_run_schema(self, workflow_id: workflow_domain.Id) -> GetWorkflowWithRunSchemaOutput:
        pass


class WorkflowMapper(BaseModel):
    use_case: type[ISpecificWorkflowUseCaseBase]
    use_case_kwargs: dict[str, Any]
    spec_for_create: type[WorkflowSpecForCreateBase]
    spec_for_run: type[WorkflowSpecForRunBase]
    domain: type[Workflow]


class WorkflowUseCase(IWorkflowUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        group_repo: group_domain.IGroupRepository,
        workflow_repo: workflow_domain.IWorkflowRepository,
        workflow_thread_repo: wf_thread_domain.IWorkflowThreadRepository,
        metering_repo: metering_domain.IMeteringRepository,
        bot_repo: bot_domain.IBotRepository,
    ):
        self.tenant_repo = tenant_repo
        self.group_repo = group_repo
        self.workflow_repo = workflow_repo
        self.workflow_thread_repo = workflow_thread_repo
        self.metering_repo = metering_repo
        self.bot_repo = bot_repo
        self.workflow_mappers = {
            WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS: WorkflowMapper(
                use_case=GenerateConstructionSpecificationsWorkflowUseCase,
                use_case_kwargs={"bot_repo": bot_repo, "workflow_repo": workflow_repo},
                spec_for_create=GenerateConstructionSpecificationsWorkflowSpecForCreate,
                spec_for_run=GenerateConstructionSpecificationsWorkflowSpecForRun,
                domain=GenerateConstructionSpecificationsWorkflow,
            ),
        }

    def _get_workflow_mapper(self, workflow_type: WorkflowType) -> WorkflowMapper:
        return self.workflow_mappers[workflow_type.root]

    def _get_workflow_use_case(self, workflow_type: WorkflowType) -> ISpecificWorkflowUseCaseBase:
        workflow_mapper = self._get_workflow_mapper(workflow_type)
        return workflow_mapper.use_case(**workflow_mapper.use_case_kwargs)

    def get_workflow_types(self) -> list[WorkflowType]:
        return [WorkflowType(root=workflow_type) for workflow_type in list(workflow_domain.WorkflowTypeEnum)]

    def get_workflow_parameters_for_create_by_type(self, workflow_type: WorkflowType) -> list[ParamSpecForCreate]:
        specific_workflow_mapper = self._get_workflow_mapper(workflow_type)
        return specific_workflow_mapper.spec_for_create.get_param_specs_for_create()

    def get_workflows_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[Workflow]:
        return self.workflow_repo.find_by_tenant_id(tenant_id)

    def get_workflows(self, input: GetCurrentUserWorkflowInput) -> list[Workflow]:
        if input.is_tenant_admin():
            return self.get_workflows_by_tenant_id(input.tenant_id)

        groups = self.group_repo.find_by_tenant_id_and_user_id(input.tenant_id, input.user_id)
        return self.workflow_repo.find_by_tenant_id_and_group_ids(
            tenant_id=input.tenant_id, group_ids=[group.id for group in groups]
        )

    def create(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        input: CreateWorkflowInput,
    ) -> None:
        specific_workflow_mapper = self._get_workflow_mapper(input.type)

        # グループが存在するか確認
        self.group_repo.get_group_by_id_and_tenant_id(group_id=group_id, tenant_id=tenant_id)

        # ワークフローのユースケースを取得する。
        specific_workflow_use_case = self._get_workflow_use_case(input.type)

        # パラメータのチェック
        specific_workflow_mapper.spec_for_create.check_is_satisfied(
            name=input.name,
            description=input.description,
            type=input.type,
            configs=input.configs,
        )

        return specific_workflow_use_case.create(group_id=group_id, input=input)

    def run(
        self,
        workflow_id: workflow_domain.Id,
        wf_thread_id: wf_thread_domain.Id | None,
        wf_thread_flow_id: wf_thread_flow_domain.Id | None,
        user_id: UserId,
        tenant_id: tenant_domain.Id,
        input: RunWorkflowInput,
    ) -> RunWorkflowOutput:
        # ワークフローを取得する。
        workflow = self.workflow_repo.find_by_id(id=workflow_id)
        # スレッドがなかったら作成する。
        if wf_thread_id is None:
            wf_thread = self.workflow_thread_repo.create(
                workflow_id=workflow_id,
                user_id=user_id,
                wf_thread_for_create=wf_thread_domain.WorkflowThreadForCreate(
                    title=wf_thread_domain.Title(root=f"{workflow.name}")
                ),
            )
        else:
            wf_thread = self.workflow_thread_repo.find_by_id(id=wf_thread_id)

        # フローがなかったら作成する。
        if wf_thread_flow_id is None:
            wf_thread_flow = self.workflow_thread_repo.create_flow(
                wf_thread_id=wf_thread.id,
                wf_thread_flow_for_create=wf_thread_flow_domain.WorkflowThreadFlowForCreate(),
            )
        # 再生成の際はinputのstepより前のステップをdeactivateする。
        else:
            wf_thread_flow = self.workflow_thread_repo.find_flow_by_id_and_thread_id(
                id=wf_thread_flow_id, wf_thread_id=wf_thread.id
            )
            # フロー内の全ステップを取得する
            active_wf_thread_flow_steps = (
                self.workflow_thread_repo.find_active_wf_thread_flow_step_by_wf_thread_flow_id(
                    wf_thread_flow_id=wf_thread_flow.id
                )
            )

            # もし、input.step以下のステップがなければupdate関数は走らせない。
            current_step = input.step
            has_step_after_input_step = False
            for step in active_wf_thread_flow_steps:
                if step.step.root >= current_step:
                    has_step_after_input_step = True
                    step.deactivate()

            # bulk-update関数を走らせる。
            if has_step_after_input_step:
                self.workflow_thread_repo.bulk_update_wf_thread_flow_step(active_wf_thread_flow_steps)

        # ワークフローのマッパーを取得する。
        workflow_mapper = self._get_workflow_mapper(workflow.type)

        # ワークフローのユースケースを取得する。
        specific_workflow_use_case = self._get_workflow_use_case(workflow.type)

        # ワークフローの仕様をチェックする。
        try:
            workflow_mapper.spec_for_run.from_domain(workflow).check_is_satisfied(step=input.step, params=input.params)
        except ValueError as e:
            raise BadRequest(str(e))

        # ワークフローを走らせる。
        output = specific_workflow_use_case.run(input=input, workflow=workflow)

        # ステップに保存
        self.workflow_thread_repo.create_flow_step(
            wf_thread_flow_id=wf_thread_flow.id,
            wf_thread_flow_step_for_create=wf_thread_flow_step_domain.WorkflowThreadFlowStepForCreate(
                step=wf_thread_flow_step_domain.Step(root=input.step),
                input=wf_thread_flow_step_domain.Input(
                    items=[
                        wf_thread_flow_step_domain.InputItem(key=param.key, value=param.value)
                        for param in input.params.items
                    ]
                ),
                output=wf_thread_flow_step_domain.Output(
                    items=[
                        wf_thread_flow_step_domain.OutputItem(key=item.key, value=item.value) for item in output.items
                    ]
                ),
                is_active=wf_thread_flow_step_domain.IsActive(root=True),
                status=wf_thread_flow_step_domain.Status.PROCESSING
                if output.use_batch_processing
                else wf_thread_flow_step_domain.Status.COMPLETED,
                token_count=output.token_count,
            ),
        )

        # OCRしたページとタイプを保存する。
        if output.di_ocr_page_count.root > 0:
            self.metering_repo.create_pdf_parser_count(
                metering=metering_domain.PdfParserMeterForCreate(
                    tenant_id=tenant_id,
                    workflow_id=workflow_id,
                    type=metering_domain.PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT,
                    quantity=metering_domain.Quantity(root=output.di_ocr_page_count.root),
                )
            )

        if output.llm_ocr_page_count.root > 0:
            self.metering_repo.create_pdf_parser_count(
                metering=metering_domain.PdfParserMeterForCreate(
                    tenant_id=tenant_id,
                    workflow_id=workflow_id,
                    type=metering_domain.PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT,
                    quantity=metering_domain.Quantity(root=output.llm_ocr_page_count.root),
                )
            )

        return output

    def get_workflow_with_run_schema(self, workflow_id: workflow_domain.Id) -> GetWorkflowWithRunSchemaOutput:
        workflow = self.workflow_repo.find_by_id(id=workflow_id)
        workflow_mapper = self._get_workflow_mapper(workflow.type)
        spec_for_run = workflow_mapper.spec_for_run.from_domain(workflow)

        return GetWorkflowWithRunSchemaOutput(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            type=workflow.type,
            configs=workflow.configs,
            schemas=spec_for_run.get_step_schemas_for_run(),
        )
