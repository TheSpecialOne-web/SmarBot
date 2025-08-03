from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from api.domain.models import common_prompt_template as cpt_domain
from api.domain.models.bot_template.id import Id as BotTemplateId
from api.libs.exceptions import NotFound

from .models.common_prompt_template import CommonPromptTemplate


class CommonPromptTemplateRepository(cpt_domain.ICommonPromptTemplateRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_by_bot_template_id(
        self,
        bot_template_id: BotTemplateId,
    ) -> list[cpt_domain.CommonPromptTemplate]:
        cpts = (
            self.session.execute(
                select(CommonPromptTemplate).where(CommonPromptTemplate.bot_template_id == bot_template_id.root)
            )
            .scalars()
            .all()
        )
        return [cpt.to_domain() for cpt in cpts]

    def find_by_id(
        self,
        bot_template_id: BotTemplateId,
        id: cpt_domain.Id,
    ) -> cpt_domain.CommonPromptTemplate:
        cpt = (
            self.session.execute(
                select(CommonPromptTemplate).where(
                    CommonPromptTemplate.id == id.root,
                    CommonPromptTemplate.bot_template_id == bot_template_id.root,
                )
            )
            .scalars()
            .first()
        )
        if cpt is None:
            raise NotFound("Common prompt template not found")
        return cpt.to_domain()

    def create(
        self,
        bot_template_id: BotTemplateId,
        common_prompt_template: cpt_domain.CommonPromptTemplateForCreate,
    ) -> cpt_domain.CommonPromptTemplate:
        new_prompt_template = CommonPromptTemplate.from_domain(
            domain_model=common_prompt_template,
            bot_template_id=bot_template_id,
        )
        try:
            self.session.add(new_prompt_template)
            self.session.commit()
            return new_prompt_template.to_domain()
        except Exception as e:
            self.session.rollback()
            raise e

    def update(
        self,
        bot_template_id: BotTemplateId,
        common_prompt_template: cpt_domain.CommonPromptTemplate,
    ) -> None:
        try:
            self.session.execute(
                update(CommonPromptTemplate)
                .where(CommonPromptTemplate.bot_template_id == bot_template_id.root)
                .where(CommonPromptTemplate.id == common_prompt_template.id.root)
                .values(
                    title=common_prompt_template.title.root,
                    prompt=common_prompt_template.prompt.root,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_ids_and_bot_template_id(self, bot_template_id: BotTemplateId, ids: list[cpt_domain.Id]) -> None:
        try:
            self.session.execute(
                delete(CommonPromptTemplate)
                .where(CommonPromptTemplate.bot_template_id == bot_template_id.root)
                .where(CommonPromptTemplate.id.in_([id.root for id in ids]))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
