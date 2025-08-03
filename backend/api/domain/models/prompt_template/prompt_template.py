import json
from pathlib import Path

from pydantic import BaseModel

from .description import Description
from .id import Id
from .prompt import Prompt
from .title import Title


class PromptTemplateProps(BaseModel):
    title: Title
    description: Description
    prompt: Prompt


class PromptTemplateForCreate(PromptTemplateProps):
    pass


class PromptTemplateForUpdate(PromptTemplateProps):
    pass


class PromptTemplate(PromptTemplateProps):
    id: Id

    def update(self, prompt_template_for_update: PromptTemplateForUpdate) -> None:
        self.title = prompt_template_for_update.title
        self.description = prompt_template_for_update.description
        self.prompt = prompt_template_for_update.prompt


class DefaultPromptTemplates(BaseModel):
    prompt_templates: list[PromptTemplateForCreate]

    def __init__(self):
        parent = Path(__file__).resolve().parent
        file_path = parent.joinpath("default_prompt_templates.json")
        with open(file_path, "r") as f:
            default_prompt_templates = json.load(f)
            pts: list[PromptTemplateForCreate] = []
            for pt in default_prompt_templates["prompt_templates"]:
                pts.append(
                    PromptTemplateForCreate(
                        title=Title(value=pt["title"]),
                        description=Description(value=pt["description"]),
                        prompt=Prompt(value=pt["prompt"]),
                    )
                )
        super().__init__(prompt_templates=pts)
