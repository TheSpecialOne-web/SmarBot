from pydantic import BaseModel, Field

from ...common_prompt_template import CommonPromptTemplate
from .description import Description
from .id import Id, create_id
from .prompt import Prompt
from .title import Title


class PromptTemplateProps(BaseModel):
    id: Id
    title: Title
    description: Description
    prompt: Prompt


class PromptTemplateForCreate(PromptTemplateProps):
    id: Id = Field(default_factory=create_id)

    @classmethod
    def from_template(cls, template: CommonPromptTemplate) -> "PromptTemplateForCreate":
        return cls(
            title=Title(root=template.title.root),
            description=Description(root=""),
            prompt=Prompt(root=template.prompt.root),
        )


class PromptTemplateForUpdate(PromptTemplateProps):
    pass


class PromptTemplate(PromptTemplateProps):
    def update(self, prompt_template_for_update: PromptTemplateForUpdate) -> None:
        self.title = prompt_template_for_update.title
        self.description = prompt_template_for_update.description
        self.prompt = prompt_template_for_update.prompt
