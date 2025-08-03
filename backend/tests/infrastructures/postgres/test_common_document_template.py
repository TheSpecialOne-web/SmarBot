from typing import Tuple
from uuid import uuid4

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot_template as bot_template_domain,
    common_document_template as cdt_domain,
)
from api.infrastructures.postgres.common_document_template import (
    CommonDocumentTemplateRepository,
)
from api.infrastructures.postgres.models.common_document_template import (
    CommonDocumentTemplate,
)
from api.libs.exceptions import NotFound


class TestCommonDocumentTemplateRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.common_document_template_repo = CommonDocumentTemplateRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_by_bot_template_id(
        self, common_document_template_seed: Tuple[list[cdt_domain.CommonDocumentTemplate], bot_template_domain.Id]
    ) -> None:
        common_document_templates, bot_template_id = common_document_template_seed
        got = self.common_document_template_repo.find_by_bot_template_id(bot_template_id)
        assert got == common_document_templates

    def test_find_by_id(
        self, common_document_template_seed: Tuple[list[cdt_domain.CommonDocumentTemplate], bot_template_domain.Id]
    ) -> None:
        common_document_templates, bot_template_id = common_document_template_seed
        for common_document_template in common_document_templates:
            got = self.common_document_template_repo.find_by_id(bot_template_id, common_document_template.id)
            assert got == common_document_template

    def test_find_by_id_not_found(
        self, common_document_template_seed: Tuple[list[cdt_domain.CommonDocumentTemplate], bot_template_domain.Id]
    ) -> None:
        common_document_templates, bot_template_id = common_document_template_seed
        with pytest.raises(NotFound):
            self.common_document_template_repo.find_by_id(bot_template_id, cdt_domain.Id(root=uuid4()))

    def test_find_by_bot_template_id_and_basename_and_file_extension(
        self, common_document_template_seed: Tuple[list[cdt_domain.CommonDocumentTemplate], bot_template_domain.Id]
    ) -> None:
        common_document_templates, bot_template_id = common_document_template_seed
        for common_document_template in common_document_templates:
            got = self.common_document_template_repo.find_by_bot_template_id_and_basename_and_file_extension(
                bot_template_id, common_document_template.basename, common_document_template.file_extension
            )
            assert got == common_document_template

    def test_create(self, bot_templates_seed: list[bot_template_domain.BotTemplate]) -> None:
        bot_template_id = bot_templates_seed[0].id

        common_document_template_for_create = cdt_domain.CommonDocumentTemplateForCreate(
            basename=cdt_domain.Basename(root="test"),
            file_extension=cdt_domain.FileExtension("pdf"),
            memo=cdt_domain.Memo(root="test"),
            data=b"test-data",
        )
        got = self.common_document_template_repo.create(bot_template_id, common_document_template_for_create)
        assert got is not None
        assert got.basename == common_document_template_for_create.basename
        assert got.file_extension == common_document_template_for_create.file_extension
        assert got.memo == common_document_template_for_create.memo

    def test_update(
        self, common_document_template_seed: Tuple[list[cdt_domain.CommonDocumentTemplate], bot_template_domain.Id]
    ) -> None:
        common_document_templates, bot_template_id = common_document_template_seed

        target_common_document_template = common_document_templates[0]
        target_common_document_template.update(
            cdt_domain.CommonDocumentTemplateForUpdate(
                memo=cdt_domain.Memo(root="updated"),
            )
        )

        self.common_document_template_repo.update(bot_template_id, target_common_document_template)

        got = self.session.execute(
            select(CommonDocumentTemplate).where(CommonDocumentTemplate.id == target_common_document_template.id.root)
        ).scalar_one_or_none()

        assert got is not None
        assert target_common_document_template.memo is not None
        assert got.memo == target_common_document_template.memo.root

    def test_delete(self, bot_templates_seed: list[bot_template_domain.BotTemplate]) -> None:
        # 削除用のコモンドキュメントテンプレートを作成
        common_document_template_for_create = cdt_domain.CommonDocumentTemplateForCreate(
            basename=cdt_domain.Basename(root="test"),
            file_extension=cdt_domain.FileExtension("pdf"),
            memo=cdt_domain.Memo(root="test"),
            data=b"test-data",
        )
        bot_template_id = bot_templates_seed[0].id
        self.session.add(
            CommonDocumentTemplate(
                id=common_document_template_for_create.id.root,
                bot_template_id=bot_template_id.root,
                basename=common_document_template_for_create.basename.root,
                file_extension=common_document_template_for_create.file_extension.value,
                memo=(
                    common_document_template_for_create.memo.root
                    if common_document_template_for_create.memo is not None
                    else None
                ),
            )
        )
        self.session.flush()

        # 削除
        self.common_document_template_repo.delete(bot_template_id, common_document_template_for_create.id)

        # 削除されているか確認
        got = self.session.execute(
            select(CommonDocumentTemplate).where(
                CommonDocumentTemplate.id == common_document_template_for_create.id.root
            )
        ).scalar_one_or_none()
        assert got is None
