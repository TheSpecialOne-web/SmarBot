from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api.domain.models import common_document_template as cdt_domain
from api.domain.models.bot_template import Id as BotTemplateId
from api.libs.exceptions import NotFound
from api.libs.logging import logging

from .models.common_document_template import CommonDocumentTemplate

logger = logging.getLogger(__name__)


class CommonDocumentTemplateRepository(cdt_domain.ICommonDocumentTemplateRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_by_bot_template_id(self, bot_template_id: BotTemplateId) -> list[cdt_domain.CommonDocumentTemplate]:
        common_document_templates = (
            self.session.execute(
                select(CommonDocumentTemplate).where(CommonDocumentTemplate.bot_template_id == bot_template_id.root)
            )
            .scalars()
            .all()
        )
        return [common_document_template.to_domain() for common_document_template in common_document_templates]

    def find_by_id(self, bot_template_id: BotTemplateId, id: cdt_domain.Id) -> cdt_domain.CommonDocumentTemplate:
        common_document_template = (
            self.session.execute(
                select(CommonDocumentTemplate).where(
                    CommonDocumentTemplate.bot_template_id == bot_template_id.root,
                    CommonDocumentTemplate.id == id.root,
                )
            )
            .scalars()
            .one_or_none()
        )
        if not common_document_template:
            raise NotFound(f"CommonDocumentTemplate not found: bot_template_id={bot_template_id.root}, id={id.root}")
        return common_document_template.to_domain()

    def find_by_bot_template_id_and_basename_and_file_extension(
        self, bot_template_id: BotTemplateId, basename: cdt_domain.Basename, file_extension: cdt_domain.FileExtension
    ) -> cdt_domain.CommonDocumentTemplate:
        common_document_template = (
            self.session.execute(
                select(CommonDocumentTemplate).where(
                    CommonDocumentTemplate.bot_template_id == bot_template_id.root,
                    CommonDocumentTemplate.basename == basename.root,
                    CommonDocumentTemplate.file_extension == file_extension.value,
                )
            )
            .scalars()
            .one_or_none()
        )
        if common_document_template is None:
            raise NotFound(
                f"CommonDocumentTemplate not found: bot_template_id={bot_template_id.root}, basename={basename.root}, file_extension={file_extension.value}"
            )
        return common_document_template.to_domain()

    def create(
        self, bot_template_id: BotTemplateId, common_document_template: cdt_domain.CommonDocumentTemplateForCreate
    ) -> cdt_domain.CommonDocumentTemplate:
        try:
            new_common_document_template = CommonDocumentTemplate.from_domain(
                domain_model=common_document_template,
                bot_template_id=bot_template_id,
            )
            self.session.add(new_common_document_template)
            self.session.commit()
        except Exception as e:
            logger.error("ドキュメントテンプレートの作成に失敗しました", exc_info=e)
            self.session.rollback()
            raise e
        return new_common_document_template.to_domain()

    def update(
        self,
        bot_template_id: BotTemplateId,
        common_document_template: cdt_domain.CommonDocumentTemplate,
    ) -> None:
        try:
            self.session.execute(
                update(CommonDocumentTemplate)
                .where(
                    CommonDocumentTemplate.bot_template_id == bot_template_id.root,
                    CommonDocumentTemplate.id == common_document_template.id.root,
                )
                .values(
                    memo=common_document_template.memo.root if common_document_template.memo else None,
                )
            )
            self.session.commit()
        except Exception as e:
            logger.error("ドキュメントテンプレートの更新に失敗しました", exc_info=e)
            self.session.rollback()
            raise e

    def delete(self, bot_template_id: BotTemplateId, id: cdt_domain.Id) -> None:
        try:
            common_document_template_to_delete = (
                self.session.execute(
                    select(CommonDocumentTemplate).where(
                        CommonDocumentTemplate.bot_template_id == bot_template_id.root,
                        CommonDocumentTemplate.id == id.root,
                    )
                )
                .scalars()
                .one_or_none()
            )
            if not common_document_template_to_delete:
                raise NotFound(
                    f"CommonDocumentTemplate not found: bot_template_id={bot_template_id.root}, id={id.root}"
                )
            common_document_template_to_delete.deleted_at = datetime.now()
            self.session.commit()
        except Exception as e:
            logger.error("ドキュメントテンプレートの削除に失敗しました", exc_info=e)
            self.session.rollback()
            raise e
