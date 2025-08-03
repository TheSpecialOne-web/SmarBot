from pydantic import BaseModel, Field

from .id import Id, create_id
from .prompt import Prompt
from .title import Title


class CommonPromptTemplateProps(BaseModel):
    title: Title
    prompt: Prompt


class CommonPromptTemplateForCreate(CommonPromptTemplateProps):
    id: Id = Field(default_factory=create_id)


class CommonPromptTemplateForUpdate(CommonPromptTemplateProps):
    pass


class CommonPromptTemplate(CommonPromptTemplateProps):
    id: Id

    def update(self, prompt_template_for_update: CommonPromptTemplateForUpdate) -> None:
        self.title = prompt_template_for_update.title
        self.prompt = prompt_template_for_update.prompt
