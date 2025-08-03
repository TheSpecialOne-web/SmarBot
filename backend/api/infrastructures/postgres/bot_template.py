from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api.domain.models import bot_template as bot_template_domain
from api.infrastructures.postgres.models.bot_template import BotTemplate
from api.libs.exceptions import NotFound


class BotTemplateRepository(bot_template_domain.IBotTemplateRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_all(self) -> list[bot_template_domain.BotTemplate]:
        bot_templates = self.session.execute(select(BotTemplate)).scalars().all()
        return [bot_template.to_domain() for bot_template in bot_templates]

    def find_by_id(self, id: bot_template_domain.Id) -> bot_template_domain.BotTemplate:
        bot_template = self.session.execute(select(BotTemplate).where(BotTemplate.id == id.root)).scalars().first()
        if bot_template is None:
            raise NotFound("BotTemplate not found")
        return bot_template.to_domain()

    def find_public(self) -> list[bot_template_domain.BotTemplate]:
        bot_templates = (
            self.session.execute(select(BotTemplate).where(BotTemplate.is_public.is_(True))).scalars().all()
        )
        return [bot_template.to_domain() for bot_template in bot_templates]

    def create(self, bot_template: bot_template_domain.BotTemplateForCreate) -> bot_template_domain.BotTemplate:
        bot_template_model = BotTemplate.from_domain(domain_model=bot_template)

        try:
            self.session.add(bot_template_model)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return bot_template_model.to_domain()

    def update(self, bot_template: bot_template_domain.BotTemplate) -> None:
        try:
            self.session.execute(
                update(BotTemplate)
                .where(BotTemplate.id == bot_template.id.root)
                .values(
                    name=bot_template.name.root,
                    description=bot_template.description.root,
                    approach=bot_template.approach.value,
                    response_generator_model_family=bot_template.response_generator_model_family.value,
                    pdf_parser=bot_template.pdf_parser.value,
                    enable_web_browsing=bot_template.enable_web_browsing.root,
                    enable_follow_up_questions=bot_template.enable_follow_up_questions.root,
                    response_system_prompt=bot_template.response_system_prompt.root,
                    document_limit=bot_template.document_limit.root,
                    is_public=bot_template.is_public.root,
                    icon_url=bot_template.icon_url.root if bot_template.icon_url else None,
                    icon_color=bot_template.icon_color.root,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, id: bot_template_domain.Id) -> None:
        try:
            bot_template_to_delete = (
                self.session.execute(select(BotTemplate).where(BotTemplate.id == id.root)).scalars().first()
            )
            if bot_template_to_delete is None:
                raise NotFound("BotTemplate not found")
            bot_template_to_delete.deleted_at = datetime.now()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
