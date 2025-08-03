from pydantic import BaseModel, Field

from api.domain.models.llm.model import ModelFamily

from ..llm.pdf_parser import PdfParser
from .approach import Approach
from .description import Description
from .document_limit import DocumentLimit
from .enable_follow_up_questions import EnableFollowUpQuestions
from .enable_web_browsing import EnableWebBrowsing
from .icon_color import IconColor
from .icon_url import IconUrl
from .id import Id, create_id
from .is_public import IsPublic
from .name import Name
from .response_system_prompt import ResponseSystemPrompt


class BotTemplateProps(BaseModel):
    name: Name
    description: Description
    approach: Approach
    pdf_parser: PdfParser
    response_generator_model_family: ModelFamily
    response_system_prompt: ResponseSystemPrompt
    document_limit: DocumentLimit
    enable_web_browsing: EnableWebBrowsing
    enable_follow_up_questions: EnableFollowUpQuestions
    is_public: IsPublic
    icon_url: IconUrl | None = None
    icon_color: IconColor


class BotTemplateForCreate(BotTemplateProps):
    id: Id = Field(default_factory=create_id)


class BotTemplateForUpdate(BotTemplateProps):
    pass


class BotTemplate(BotTemplateProps):
    id: Id

    def update(self, bot_template_for_update: BotTemplateForUpdate) -> None:
        self.name = bot_template_for_update.name
        self.description = bot_template_for_update.description
        self.approach = bot_template_for_update.approach
        self.pdf_parser = bot_template_for_update.pdf_parser
        self.response_generator_model_family = bot_template_for_update.response_generator_model_family
        self.response_system_prompt = bot_template_for_update.response_system_prompt
        self.document_limit = bot_template_for_update.document_limit
        self.enable_web_browsing = bot_template_for_update.enable_web_browsing
        self.enable_follow_up_questions = bot_template_for_update.enable_follow_up_questions
        self.is_public = bot_template_for_update.is_public
        self.icon_color = bot_template_for_update.icon_color

    def update_icon_url(self, icon_url: IconUrl | None):
        self.icon_url = icon_url
