from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from api.domain.models import common_document_template as cdt_domain
from api.domain.models.bot_template import Id as BotTemplateId
from api.usecase.common_document_template import CommonDocumentTemplateUseCase


class TestCommonDocumentTemplateUsecase:
    @pytest.fixture
    def setup(self):
        self.bot_template_repo = Mock()
        self.common_document_template_repo = Mock()
        self.blob_storage_service = Mock()
        self.common_document_template_usecase = CommonDocumentTemplateUseCase(
            self.bot_template_repo,
            self.common_document_template_repo,
            self.blob_storage_service,
        )

    def test_find_common_document_templates_by_bot_template_id(self):
        """bot_template_idからコモンドキュメントテンプレートを取得できることを確認する"""
        want = [
            cdt_domain.CommonDocumentTemplate(
                id=cdt_domain.Id(root=uuid4()),
                basename=cdt_domain.Basename(root="test"),
                memo=cdt_domain.Memo(root="test"),
                file_extension=cdt_domain.FileExtension("test"),
                created_at=cdt_domain.CreatedAt(root=datetime.now()),
            )
        ]
        bot_template_id = BotTemplateId(root=uuid4())
        self.common_document_template_usecase.common_document_template_repo.find_by_bot_template_id.return_value = want
        got = self.common_document_template_usecase.find_common_document_templates_by_bot_template_id(bot_template_id)
        self.common_document_template_usecase.bot_template_repo.find_by_id.assert_called_once_with(bot_template_id)
        self.common_document_template_usecase.common_document_template_repo.find_by_bot_template_id.assert_called_once_with(
            bot_template_id
        )

        assert got == want

    def test_create_common_document_template(self):
        """ドキュメントテンプレートが作成できることを確認する"""

        common_document_template_for_create = cdt_domain.CommonDocumentTemplateForCreate(
            memo=cdt_domain.Memo(root="test"),
            basename=cdt_domain.Basename(root="test"),
            file_extension=cdt_domain.FileExtension("txt"),
            data=b"test data",
        )
        bot_template_id = BotTemplateId(root=uuid4())
        self.common_document_template_usecase.create_common_document_template(
            bot_template_id=bot_template_id, common_document_templates_for_create=[common_document_template_for_create]
        )
        self.common_document_template_usecase.common_document_template_repo.create.assert_called_once_with(
            bot_template_id=bot_template_id, common_document_template=common_document_template_for_create
        )
        self.common_document_template_usecase.blob_storage_service.upload_common_document_template_to_common_container.assert_called_once_with(
            bot_template_id=bot_template_id, common_document_template=common_document_template_for_create
        )

    def test_update_common_document_template(self):
        """ドキュメントテンプレートが更新できることを確認する"""

        common_document_template_for_update = cdt_domain.CommonDocumentTemplateForUpdate(
            memo=cdt_domain.Memo(root="updated memo")
        )
        bot_template_id = BotTemplateId(root=uuid4())
        common_document_template = cdt_domain.CommonDocumentTemplate(
            id=cdt_domain.Id(root=uuid4()),
            basename=cdt_domain.Basename(root="test"),
            memo=cdt_domain.Memo(root="test"),
            file_extension=cdt_domain.FileExtension("txt"),
            created_at=cdt_domain.CreatedAt(root=datetime.now()),
        )

        common_document_template.update(common_document_template=common_document_template_for_update)
        self.common_document_template_usecase.common_document_template_repo.find_by_id.return_value = (
            common_document_template
        )

        self.common_document_template_usecase.update_common_document_template(
            bot_template_id=bot_template_id,
            id=common_document_template.id,
            common_document_template_for_update=common_document_template_for_update,
        )

        self.common_document_template_usecase.common_document_template_repo.find_by_id.assert_called_once_with(
            bot_template_id=bot_template_id, id=common_document_template.id
        )
        self.common_document_template_usecase.common_document_template_repo.update.assert_called_once_with(
            bot_template_id=bot_template_id, common_document_template=common_document_template
        )
        assert common_document_template.memo == common_document_template_for_update.memo

    def test_delete_common_document_template(self):
        """ドキュメントテンプレートが削除できることを確認する"""

        bot_template_id = BotTemplateId(root=uuid4())
        common_document_template = cdt_domain.CommonDocumentTemplate(
            id=cdt_domain.Id(root=uuid4()),
            basename=cdt_domain.Basename(root="test"),
            memo=cdt_domain.Memo(root="test"),
            file_extension=cdt_domain.FileExtension("txt"),
            created_at=cdt_domain.CreatedAt(root=datetime.now()),
        )

        self.common_document_template_usecase.common_document_template_repo.find_by_id.return_value = (
            common_document_template
        )

        self.common_document_template_usecase.delete_common_document_template(
            bot_template_id=bot_template_id,
            id=common_document_template.id,
        )

        self.common_document_template_usecase.common_document_template_repo.find_by_id.assert_called_once_with(
            bot_template_id=bot_template_id, id=common_document_template.id
        )
        self.common_document_template_usecase.common_document_template_repo.delete.assert_called_once_with(
            bot_template_id=bot_template_id, id=common_document_template.id
        )
        self.common_document_template_usecase.blob_storage_service.delete_common_document_template_from_common_container.assert_called_once_with(
            bot_template_id=bot_template_id,
            common_document_template=common_document_template,
        )

    def test_get_url_by_bot_template_id_and_id(self):
        """bot_template_idとidからコモンドキュメントテンプレートのURLを取得できることを確認する"""
        want = cdt_domain.Url(root="https://test.com")
        bot_template_id = BotTemplateId(root=uuid4())
        self.common_document_template_usecase.blob_storage_service.create_common_document_template_url.return_value = (
            want
        )
        got = self.common_document_template_usecase.get_url_by_bot_template_id_and_id(
            bot_template_id=bot_template_id, id=cdt_domain.Id(root=uuid4())
        )
        self.common_document_template_usecase.blob_storage_service.create_common_document_template_url.assert_called_once_with(
            bot_template_id=bot_template_id, id=cdt_domain.Id(root=uuid4())
        )
        assert got == want
