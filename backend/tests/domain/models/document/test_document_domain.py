from datetime import datetime
from uuid import uuid4

from api.domain.models import (
    document as document_domain,
    document_folder as document_folder_domain,
    user as user_domain,
)


def dummy_document(id: document_domain.Id, document_folder_id: document_folder_domain.Id):
    return document_domain.Document(
        id=id,
        document_folder_id=document_folder_id,
        name=document_domain.Name(value="テストファイル"),
        memo=document_domain.Memo(value="テストメモ"),
        file_extension=document_domain.FileExtension.PDF,
        status=document_domain.Status.PENDING,
        storage_usage=document_domain.StorageUsage(root=100),
        creator_id=user_domain.Id(value=1),
        created_at=document_domain.CreatedAt(value=datetime.now()),
    )


class TestDocumentDomain:
    pass


class TestDocumentWithAncestorFolders:
    def test_get_full_path(self):
        document = dummy_document(document_domain.Id(value=1), document_folder_domain.Id(root=uuid4()))
        document_with_ancestor_folders = document_domain.DocumentWithAncestorFolders(
            **document.model_dump(),
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=document_folder_domain.Id(root=uuid4()),
                    name=document_folder_domain.Name(root="テストフォルダ1層目"),
                    order=document_folder_domain.Order(root=1),
                    created_at=document_folder_domain.CreatedAt(root=datetime.now()),
                ),
                document_folder_domain.DocumentFolderWithOrder(
                    id=document_folder_domain.Id(root=uuid4()),
                    name=document_folder_domain.Name(root="テストフォルダ2層目"),
                    order=document_folder_domain.Order(root=2),
                    created_at=document_folder_domain.CreatedAt(root=datetime.now()),
                ),
            ],
        )
        assert (
            document_with_ancestor_folders.get_full_path() == "テストフォルダ1層目/テストフォルダ2層目/テストファイル"
        )
