import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.document import feedback as document_feedback_domain
from api.infrastructures.postgres.document import DocumentRepository
from api.infrastructures.postgres.models.document import Document
from api.infrastructures.postgres.models.user_document import UserDocument
from api.libs.exceptions import NotFound
from tests.conftest import DocumentFolderSeed, DocumentsWithAncestorFoldersSeed

BotsSeed = tuple[list[bot_domain.Bot], list[dict], tenant_domain.Tenant]
DocumentSeed = tuple[document_domain.Document, document_domain.DocumentForCreate, bot_domain.Id]
DocumentsSeed = tuple[list[document_domain.Document], bot_domain.Id]
UserSeed = tuple[user_domain.Id, user_domain.UserForCreate, tenant_domain.Id, str, user_domain.Id]
UserDocumentSeed = tuple[document_feedback_domain.DocumentFeedback, user_domain.Id, document_domain.Id]


class TestDocumentRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.document_repo = DocumentRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self, document_seed: DocumentSeed):
        """新しいドキュメントを作成するテスト"""
        new_document, _, new_bot_id = document_seed

        # データベースに新しいドキュメントが保存されていることを確認
        saved_document = self.document_repo.find_by_id_and_bot_id(new_document.id, new_bot_id)
        assert saved_document == new_document

    def test_find_by_id(self, document_seed: DocumentSeed):
        """存在するdocument.id"""
        new_document, _, new_bot_id = document_seed

        document = self.document_repo.find_by_id_and_bot_id(new_document.id, new_bot_id)

        assert document == new_document

    def test_find_by_id_not_found(self):
        """存在しないdocument.idとbot.id"""
        non_existent_document_id = document_domain.Id(value=9999)
        non_existent_bot_id = bot_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.document_repo.find_by_id_and_bot_id(non_existent_document_id, non_existent_bot_id)

    def test_find_by_bot_id(self, document_seed: DocumentSeed):
        """bot_idがあるケース"""
        new_document, _, bot_id = document_seed

        documents = self.document_repo.find_by_bot_id(bot_id)
        # ドキュメントが存在することを確認
        assert documents == [new_document]

    def test_find_by_bot_id_not_found(self):
        """bot_idが見つからないケース"""
        non_existent_bot_id = bot_domain.Id(value=9999)

        documents = self.document_repo.find_by_bot_id(non_existent_bot_id)
        assert documents == []

    def test_update(self, document_seed: DocumentSeed):
        """update関数を実行し、ドキュメントが更新されているかを検証"""

        new_document, _, new_bot_id = document_seed

        # 新しいドキュメントが正しく作成されたことを確認
        assert new_document is not None
        assert new_document.name.value == "テストドキュメント"
        # データベースに新しいドキュメントが保存されていることを確認
        saved_document = self.document_repo.find_by_id_and_bot_id(new_document.id, new_bot_id)
        assert saved_document is not None
        assert saved_document.name.value == "テストドキュメント"

        updated_document = document_domain.Document(
            id=new_document.id,
            name=new_document.name,
            memo=document_domain.Memo(value="memo-update"),
            file_extension=new_document.file_extension,
            status=new_document.status,
            created_at=new_document.created_at,
            storage_usage=new_document.storage_usage,
            creator_id=new_document.creator_id,
            document_folder_id=new_document.document_folder_id,
        )

        self.document_repo.update(document=updated_document)

        # ドキュメントが更新されたことを確認します。
        document = (
            self.session.execute(
                select(Document).filter_by(id=new_document.id.value).execution_options(include_deleted=True)
            )
            .scalars()
            .first()
        )
        assert document is not None
        assert document.to_domain() == updated_document

    def test_bulk_update(self, documents_seed: DocumentsSeed):
        """bulk_update関数を実行し、ドキュメントが更新されているかを検証"""

        new_documents, bot_id = documents_seed

        # 新しいドキュメントが正しく作成されたことを確認
        assert new_documents is not None
        assert new_documents[0].name.value == "テストドキュメント"
        assert new_documents[1].name.value == "テストドキュメント2"
        # データベースに新しいドキュメントが保存されていることを確認
        saved_documents = self.document_repo.find_by_ids_and_bot_id(
            bot_id=bot_id, document_ids=[document.id for document in new_documents]
        )
        assert saved_documents is not None
        assert saved_documents[0].name.value == "テストドキュメント"
        assert saved_documents[1].name.value == "テストドキュメント2"

        self.document_repo.bulk_update(
            documents=[
                document_domain.Document(
                    id=document.id,
                    name=document.name,
                    memo=document_domain.Memo(value=f"memo-update{i}"),
                    file_extension=document.file_extension,
                    status=document_domain.Status.DELETING,
                    created_at=document.created_at,
                    storage_usage=document.storage_usage,
                    creator_id=document.creator_id,
                    document_folder_id=document.document_folder_id,
                )
                for i, document in enumerate(new_documents)
            ]
        )

        # ドキュメントが更新されたことを確認します。
        documents = (
            self.session.execute(
                select(Document)
                .where(Document.id.in_([document.id.value for document in new_documents]))
                .execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert documents is not None
        for i in range(len(documents)):
            assert documents[i].memo == f"memo-update{i}"
            assert documents[i].status == document_domain.Status.DELETING

    def test_delete(self, document_folder_seed: DocumentFolderSeed):
        """delete関数を実行し、ドキュメントが論理削除されているかを検証"""
        root_folder, _, _, bot_id = document_folder_seed
        document_for_create = document_domain.DocumentForCreate(
            name=document_domain.Name(value="テストドキュメント"),
            memo=document_domain.Memo(value="テストドキュメントのメモ"),
            file_extension=document_domain.FileExtension.PDF,
            data=b"test",
            creator_id=user_domain.Id(value=1),
        )
        new_document = self.document_repo.create(bot_id, root_folder.id, document_for_create)

        self.document_repo.delete(new_document.id)

        # ドキュメントが論理削除されたことを確認します。
        with pytest.raises(NotFound):
            self.document_repo.find_by_id_and_bot_id(new_document.id, bot_id)

    def test_delete_not_found(self):
        """存在しないdocument_idを渡すとNotFound例外が発生することをテスト"""
        invalid_document_id = document_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.document_repo.delete(invalid_document_id)

    @pytest.mark.parametrize("documents_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_document_folder_ids(self, documents_seed: DocumentsSeed):
        new_documents, bot_id = documents_seed

        self.document_repo.delete_by_bot_id(bot_id)
        self.document_repo.hard_delete_by_document_folder_ids(
            [new_doc.document_folder_id for new_doc in new_documents]
        )

        documents = (
            self.session.execute(
                select(Document).where(Document.bot_id == bot_id.value).execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(documents) == 0

    def test_find_by_ids_and_bot_id(self, documents_seed):
        """特定のbot_idとdocument_idsに基づいてドキュメントを検索し、期待されるドキュメントが取得できることを確認するテスト。"""
        new_documents, bot_id = documents_seed

        # 検索メソッドの実行
        documents = self.document_repo.find_by_ids_and_bot_id(bot_id, [document.id for document in new_documents])

        # 期待されるドキュメントが取得できているか確認
        assert documents == new_documents

    def test_find_by_bot_id_and_parent_document_folder_id(self, documents_seed):
        """特定のbot_idとparent_document_folder_idに基づいてドキュメントを検索し、期待されるドキュメントが取得できることを確認するテスト。"""
        new_documents, bot_id = documents_seed

        # 検索メソッドの実行
        documents = self.document_repo.find_by_bot_id_and_parent_document_folder_id(
            bot_id, new_documents[0].document_folder_id
        )

        # 期待されるドキュメントが取得できているか確認
        assert documents == new_documents

    def test_find_feedback_by_id_and_user_id(self, user_document_seed: UserDocumentSeed):
        # Input
        user_document, user_id, document_id = user_document_seed

        # Execute
        got = self.document_repo.find_feedback_by_id_and_user_id(document_id, user_id)

        # Assert
        assert got == user_document

    def test_create_feedback(self, user_seed: UserSeed, documents_seed: DocumentsSeed):
        # Input
        user_id, _, _, _, _ = user_seed
        documents, _ = documents_seed
        document = documents[0]
        user_document = document_feedback_domain.DocumentFeedback(
            user_id=user_id,
            document_id=document.id,
            evaluation=document_feedback_domain.Evaluation.BAD,
        )

        # Execute
        got = self.document_repo.create_feedback(user_document)

        # Assert
        assert got == user_document

    def test_update_feedback(self, user_document_seed: UserDocumentSeed):
        # Input
        user_document, _, document_id = user_document_seed
        assert user_document.evaluation == document_feedback_domain.Evaluation.GOOD
        user_document.evaluation = document_feedback_domain.Evaluation.BAD

        # Execute
        self.document_repo.update_feedback(user_document)

        # Assert
        updated_user_document = self.session.execute(
            select(UserDocument)
            .where(UserDocument.document_id == document_id.value)
            .where(UserDocument.user_id == user_document.user_id.value)
        ).scalar_one()
        assert updated_user_document.evaluation == document_feedback_domain.Evaluation.BAD

    @pytest.mark.parametrize("documents_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_by_bot_id(self, documents_seed: DocumentsSeed):
        _, bot_id = documents_seed

        self.document_repo.delete_by_bot_id(bot_id)

        documents = self.document_repo.find_by_bot_id(bot_id)
        assert len(documents) == 0

    def test_find_all_descendants_documents_by_ancestor_folder_id_without_deleting(
        self, documents_with_ancestor_folders_seed: DocumentsWithAncestorFoldersSeed
    ):
        """
        各フォルダレベルで、そのフォルダ以下のすべてのドキュメントが取得できることをテストします。

        root_folder/ -> すべてのドキュメントが取得できる
        ├── child_folder/ -> child_documentとchild_child_documentが取得できる
        │   └── child_child_folder/ -> child_child_documentのみが取得できる
        """
        document_with_ancestor_folders, bot_id = documents_with_ancestor_folders_seed

        # root_folderのテスト - すべてのドキュメントが取得できる
        root_folder_id = document_with_ancestor_folders[0].ancestor_folders[0].id
        got_root = self.document_repo.find_all_descendants_documents_by_ancestor_folder_id(
            ancestor_folder_id=root_folder_id, bot_id=bot_id
        )
        documents = [document_domain.Document(**document.model_dump()) for document in document_with_ancestor_folders]
        assert got_root == documents  # すべてのドキュメントが含まれる

        # child_folderのテスト - 2つのドキュメントが取得できる
        child_folder_id = document_with_ancestor_folders[1].ancestor_folders[1].id
        got_child = self.document_repo.find_all_descendants_documents_by_ancestor_folder_id(
            ancestor_folder_id=child_folder_id, bot_id=bot_id
        )
        documents = [
            document_domain.Document(**document.model_dump()) for document in document_with_ancestor_folders[1:]
        ]
        assert got_child == documents  # child_documentとchild_child_documentが含まれる

        # child_child_folderのテスト - 1つのドキュメントが取得できる
        child_child_folder_id = document_with_ancestor_folders[2].ancestor_folders[2].id
        got_child_child = self.document_repo.find_all_descendants_documents_by_ancestor_folder_id(
            ancestor_folder_id=child_child_folder_id, bot_id=bot_id
        )
        documents = [
            document_domain.Document(**document.model_dump()) for document in document_with_ancestor_folders[2:]
        ]
        assert got_child_child == documents  # child_child_documentのみが含まれる
