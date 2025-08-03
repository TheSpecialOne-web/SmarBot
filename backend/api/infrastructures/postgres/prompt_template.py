from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from api.domain.models import (
    prompt_template as domain,
    tenant as tenant_domain,
)
from api.libs.exceptions import NotFound

from .models.prompt_template import PromptTemplate


class PromptTemplateRepository(domain.IPromptTemplateRepository):
    def __init__(self, session: Session):
        self.session = session

    def bulk_create(
        self,
        tenant_id: tenant_domain.Id,
        prompt_templates: list[domain.PromptTemplateForCreate],
    ) -> list[domain.PromptTemplate]:
        pts = [PromptTemplate.from_domain(domain_model=pt, tenant_id=tenant_id) for pt in prompt_templates]

        try:
            self.session.add_all(pts)
            self.session.commit()
            return [pt.to_domain() for pt in pts]
        except Exception as e:
            self.session.rollback()
            raise e

    def find_by_tenant_id(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[domain.PromptTemplate]:
        pts = self.session.execute(select(PromptTemplate).filter_by(tenant_id=tenant_id.value)).scalars().all()
        prompt_templates = []
        for pt in pts:
            if not isinstance(pt, PromptTemplate):
                continue
            prompt_templates.append(pt.to_domain())
        return prompt_templates

    def find_by_id_and_tenant_id(
        self,
        id: domain.Id,
        tenant_id: tenant_domain.Id,
    ) -> domain.PromptTemplate:
        pt = (
            self.session.execute(select(PromptTemplate).filter_by(id=id.value, tenant_id=tenant_id.value))
            .scalars()
            .first()
        )
        if not pt or not isinstance(pt, PromptTemplate):
            raise NotFound("プロンプトテンプレートが見つかりませんでした。")
        return pt.to_domain()

    def update(
        self,
        prompt_template: domain.PromptTemplate,
    ) -> None:
        try:
            self.session.execute(
                update(PromptTemplate)
                .where(PromptTemplate.id == prompt_template.id.value)
                .values(
                    title=prompt_template.title.value,
                    description=prompt_template.description.value,
                    prompt=prompt_template.prompt.value,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_ids_and_tenant_id(
        self,
        ids: list[domain.Id],
        tenant_id: tenant_domain.Id,
    ) -> None:
        try:
            self.session.execute(
                delete(PromptTemplate)
                .where(PromptTemplate.id.in_([id.value for id in ids]))
                .where(PromptTemplate.tenant_id == tenant_id.value)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_tenant_id(self, tenant_id: tenant_domain.Id) -> None:
        try:
            self.session.execute(
                update(PromptTemplate)
                .where(PromptTemplate.tenant_id == tenant_id.value)
                .values(deleted_at=datetime.now(timezone.utc))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_tenant_id(self, tenant_id: tenant_domain.Id) -> None:
        try:
            self.session.execute(
                delete(PromptTemplate)
                .where(PromptTemplate.tenant_id == tenant_id.value)
                .where(PromptTemplate.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
