from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, RootModel, StrictBool, StrictInt

from api.domain.models import (
    workflow as workflow_domain,
)
from api.domain.models.group import Id as GroupId
from api.domain.models.token import TokenCount
from api.domain.models.workflow import RunStepParams

specific_workflow_domain = TypeVar("specific_workflow_domain")


class CreateWorkflowInput(BaseModel):
    name: workflow_domain.Name
    description: workflow_domain.Description
    type: workflow_domain.WorkflowType
    configs: workflow_domain.WorkflowConfigList


class RunWorkflowInput(BaseModel):
    step: int
    params: RunStepParams


class RunWorkflowItem(BaseModel):
    key: str
    value: Any


class UseBatchProcessing(RootModel):
    root: StrictBool


class DIOcrPageCount(RootModel):
    root: StrictInt


class LLMOcrPageCount(RootModel):
    root: StrictInt


class RunWorkflowOutput(BaseModel):
    items: list[RunWorkflowItem]
    token_count: TokenCount
    di_ocr_page_count: DIOcrPageCount
    llm_ocr_page_count: LLMOcrPageCount
    use_batch_processing: UseBatchProcessing

    def get_value(self, key: str) -> Any:
        for result in self.items:
            if result.key == key:
                return result.value
        raise ValueError(f"Key '{key}' not found in this step.")


class ISpecificWorkflowUseCaseBase(ABC, Generic[specific_workflow_domain]):
    """
    特定のワークフロータイプに固有の操作を定義する基底クラス

    Genericsを使用して、戻り値の型と入力の型を柔軟に定義
    """

    @abstractmethod
    def create(self, group_id: GroupId, input: CreateWorkflowInput) -> None:
        """args:
        group_id: グループID
        input: ワークフローを作成するための入力
        """
        """
        ワークフローを作成するためのメソッド

        各ワークフロータイプで具体的な実装を提供
        """
        pass

    @abstractmethod
    def run(self, input: RunWorkflowInput, workflow: specific_workflow_domain) -> RunWorkflowOutput:
        """args:
        input: ワークフローを実行するための入力
        workflow: 具体的なワークフローのドメイン
        """
        """
        ワークフローを実行するためのメソッド

        各ワークフロータイプで具体的な実装を提供

        Returns:
            RunWorkflowOutput: ワークフローの実行結果
        """
        # pass だと エラーになるため NotImplementedError を返す
        raise NotImplementedError
