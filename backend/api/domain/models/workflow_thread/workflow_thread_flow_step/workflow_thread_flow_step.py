from pydantic import BaseModel, Field

from ...token import TokenCount
from .id import Id, create_id
from .input import Input
from .is_active import IsActive
from .output import Output
from .status import Status
from .step import Step


class WorkflowThreadFlowStepProps(BaseModel):
    step: Step
    input: Input
    output: Output
    is_active: IsActive
    status: Status
    token_count: TokenCount


class WorkflowThreadFlowStep(WorkflowThreadFlowStepProps):
    id: Id

    def update_status_to_completed(self):
        self.status = Status.COMPLETED

    def update_status_to_failed(self):
        self.status = Status.FAILED

    def activate(self):
        self.is_active = IsActive(root=True)

    def deactivate(self):
        self.is_active = IsActive(root=False)

    def update_output(self, output: Output):
        self.output = output

    def add_token_count(self, token_count: TokenCount):
        self.token_count = TokenCount(root=self.token_count.root + token_count.root)


class WorkflowThreadFlowStepForCreate(WorkflowThreadFlowStepProps):
    id: Id = Field(default_factory=create_id)
