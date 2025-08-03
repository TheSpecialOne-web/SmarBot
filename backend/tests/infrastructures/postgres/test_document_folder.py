from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from api.database import SessionFactory
from api.domain.models import (
    bot as bot_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
)
from api.domain.models.document_folder import external_data_connection as external_document_folder_domain
from api.domain.models.llm.model import ModelFamily
from api.domain.models.storage.container_name import ContainerName
from api.domain.models.tenant import (
    external_data_connection as external_data_connection_domain,
)
from api.infrastructures.postgres.document_folder import DocumentFolderRepository
from api.infrastructures.postgres.models.bot import Bot
from api.infrastructures.postgres.models.document_folder import DocumentFolder
from api.infrastructures.postgres.models.document_folder_path import DocumentFolderPath
from tests.conftest import DocumentFolderSeed, ExternalDocumentFolderSeed


class TestDocumentFolderRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.document_folder_repo = DocumentFolderRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def teat_find_root_document_folder_by_bot_id(self, document_folder_seed: DocumentFolderSeed):
        # input
        root_document_folder, _, _, bot_id = document_folder_seed
        # execute
        got = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id=bot_id)
        # assert
        assert got == root_document_folder

    def test_find_by_id_and_bot_id(self, document_folder_seed: DocumentFolderSeed):
        # input
        root_document_folder, _, _, bot_id = document_folder_seed
        # execute
        got = self.document_folder_repo.find_by_id_and_bot_id(
            document_folder_id=root_document_folder.id, bot_id=bot_id
        )
        # assert
        assert got == root_document_folder

    def test_find_by_parent_document_folder_id(self, document_folder_seed: DocumentFolderSeed):
        # input
        root_document_folder, child_document_folders, _, bot_id = document_folder_seed
        # execute
        got = self.document_folder_repo.find_by_parent_document_folder_id(
            bot_id=bot_id,
            parent_document_folder_id=root_document_folder.id,
        )
        # assert
        assert got == child_document_folders

    def test_find_descendants_by_id(self, document_folder_seed: DocumentFolderSeed):
        # input
        (
            root_document_folder,
            child_document_folders,
            child_child_document_folders,
            bot_id,
        ) = document_folder_seed
        # execute
        got = self.document_folder_repo.find_descendants_by_id(
            bot_id=bot_id,
            id=root_document_folder.id,
        )
        # assert
        assert got == child_child_document_folders + child_document_folders

    def test_find_by_parent_document_folder_id_and_name(self, document_folder_seed: DocumentFolderSeed):
        # Input
        parent_document_folder, child_document_folders, _, _ = document_folder_seed
        name = child_document_folders[0].name
        if name is None:
            name = document_folder_domain.Name(root="document_folder_seed_name2")

        # Expected
        expected_output = [child_document_folders[0]]

        # Execute
        output = self.document_folder_repo.find_by_parent_document_folder_id_and_name(
            parent_document_folder_id=parent_document_folder.id,
            name=name,
        )

        # Assert
        assert output == expected_output

    def test_find_by_bot_ids(self, document_folder_seed: DocumentFolderSeed):
        (
            root_document_folder,
            child_document_folders,
            child_child_document_folders,
            bot_id,
        ) = document_folder_seed

        want = sorted(
            [
                root_document_folder,
                *child_document_folders,
                *child_child_document_folders,
            ],
            key=lambda x: x.created_at.root,
        )

        got = self.document_folder_repo.find_by_bot_ids(bot_ids=[bot_id])
        got = sorted(got, key=lambda x: x.created_at.root)

        assert got == want

    def test_find_external_document_folder_by_id_and_bot_id(
        self, external_document_folder_seed: ExternalDocumentFolderSeed
    ):
        external_document_folder, folder_id, bot_id = external_document_folder_seed

        got = self.document_folder_repo.find_external_document_folder_by_id_and_bot_id(id=folder_id, bot_id=bot_id)

        assert isinstance(got, external_document_folder_domain.ExternalDocumentFolder)
        assert got == external_document_folder

    def test_create(self, document_folder_seed: DocumentFolderSeed):
        # Input
        parent_document_folder, _, _, bot_id = document_folder_seed
        document_folder_for_create = document_folder_domain.DocumentFolderForCreate(
            name=document_folder_domain.Name(root="test_create_document_folder_name"),
        )

        # Execute
        output = self.document_folder_repo.create(
            bot_id=bot_id,
            parent_document_folder_id=parent_document_folder.id,
            document_folder=document_folder_for_create,
        )

        # Expected
        expected_output = document_folder_domain.DocumentFolder(
            id=document_folder_for_create.id,
            name=document_folder_for_create.name,
            created_at=output.created_at,
        )

        # Assert
        assert output == expected_output

    def test_create_external_document_folder(self, document_folder_seed: DocumentFolderSeed):
        # Input
        parent_document_folder, _, _, bot_id = document_folder_seed
        document_folder_for_create = document_folder_domain.ExternalDocumentFolderForCreate(
            name=document_folder_domain.Name(root="test_create_document_folder_name"),
            external_id=external_data_connection_domain.ExternalId(root="b35biy34fiy3"),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
            sync_schedule=external_data_connection_domain.SyncSchedule(root="0 15 * * *"),
            external_sync_metadata=external_data_connection_domain.ExternalSyncMetadata(
                root={
                    "delta_token": "test_delta_token",
                }
            ),
            last_synced_at=external_data_connection_domain.LastSyncedAt(root=datetime.now()),
        )

        # Execute
        output = self.document_folder_repo.create_external_document_folder(
            bot_id=bot_id,
            parent_document_folder_id=parent_document_folder.id,
            external_document_folder=document_folder_for_create,
        )

        # Expected
        expected_output = document_folder_domain.DocumentFolder(
            id=document_folder_for_create.id,
            name=document_folder_for_create.name,
            created_at=output.created_at,
            external_id=document_folder_for_create.external_id,
            external_type=document_folder_for_create.external_type,
            external_updated_at=document_folder_for_create.external_updated_at,
            sync_schedule=document_folder_for_create.sync_schedule,
            last_synced_at=output.last_synced_at,
        )

        # Assert
        assert output == expected_output

    def test_update(self, document_folder_seed: DocumentFolderSeed):
        # Input
        _, child_document_folders, _, bot_id = document_folder_seed
        document_folder = child_document_folders[0]

        document_folder_for_update = document_folder_domain.DocumentFolderForUpdate(
            name=document_folder_domain.Name(root="test_update_document_folder_name"),
        )

        # Expected
        expected_output = document_folder_domain.DocumentFolder(
            id=document_folder.id,
            name=document_folder_for_update.name,
            created_at=document_folder.created_at,
        )

        # Execute
        output = self.document_folder_repo.update(
            bot_id=bot_id,
            document_folder=document_folder_domain.DocumentFolder(
                id=document_folder.id,
                name=document_folder_for_update.name,
                created_at=document_folder.created_at,
            ),
        )

        # Assert
        assert output == expected_output

    def test_delete_by_ids(self, document_folder_seed: DocumentFolderSeed):
        # Input
        _, child_document_folders, _, bot_id = document_folder_seed
        document_folder_id = child_document_folders[0].id

        # Execute
        self.document_folder_repo.delete_by_ids(bot_id=bot_id, document_folder_ids=[document_folder_id])

        # Test
        deleted_document_folder = self.session.execute(
            select(DocumentFolder).where(DocumentFolder.id == document_folder_id.root)
        ).scalar_one_or_none()
        deleted_document_folder_paths = (
            self.session.execute(
                select(DocumentFolderPath).where(
                    DocumentFolderPath.descendant_document_folder_id == document_folder_id.root
                )
            )
            .scalars()
            .all()
        )

        assert deleted_document_folder is None
        assert deleted_document_folder_paths == []

    def test_create_root_document_folder(self, tenant_seed):
        # bot作成
        bot_for_create = bot_domain.BotForCreate(
            name=bot_domain.Name(value="test_create_root_document_folder_bot_name"),
            description=bot_domain.Description(value="test_create_root_document_folder_bot_description"),
            index_name=None,
            container_name=ContainerName(root="test-container-name"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[
                bot_domain.ExampleQuestion(value="test_create_root_document_folder_bot_example_question")
            ],
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            response_generator_model_family=ModelFamily.GEMINI_15_PRO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=bot_domain.IconUrl(root="test_create_root_document_folder_bot_icon_url"),
            icon_color=bot_domain.IconColor(root="test_create_root_document_folder_bot_icon_color"),
            endpoint_id=bot_domain.EndpointId(root=uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

        new_bot = Bot(
            tenant_id=tenant_seed.id.value,
            group_id=group_domain.Id(value=1).value,
            name=bot_for_create.name.value,
            description=bot_for_create.description.value,
            index_name=bot_for_create.index_name.root if bot_for_create.index_name else "",
            container_name=bot_for_create.container_name.root if bot_for_create.container_name else "",
            approach=bot_for_create.approach.value,
            example_questions=[example_question.value for example_question in bot_for_create.example_questions],
            search_method=bot_for_create.search_method.value if bot_for_create.search_method else "",
            response_generator_model_family=bot_for_create.response_generator_model_family.value,
            image_generator_model_family=(
                bot_for_create.image_generator_model_family.value
                if bot_for_create.image_generator_model_family
                else ""
            ),
            pdf_parser=bot_for_create.pdf_parser.value if bot_for_create.pdf_parser else "",
            enable_web_browsing=bot_for_create.enable_web_browsing.root,
            enable_follow_up_questions=bot_for_create.enable_follow_up_questions.root,
            status=bot_domain.Status.ACTIVE.value,
            data_source_id=uuid4(),
            icon_url=bot_for_create.icon_url.root if bot_for_create.icon_url else None,
            icon_color=bot_for_create.icon_color.root,
        )

        self.session.add(new_bot)
        self.session.commit()
        bot = new_bot.to_domain(approach_variable_dtos=[])

        document_folder_for_create = document_folder_domain.RootDocumentFolderForCreate(
            name=None,
        )

        # Execute
        output = self.document_folder_repo.create_root_document_folder(
            bot_id=bot.id,
            root_document_folder_for_create=document_folder_for_create,
        )

        # created_atはテスト対象外
        expected_output = document_folder_domain.DocumentFolder(
            id=document_folder_for_create.id,
            name=document_folder_for_create.name,
            created_at=output.created_at,
        )

        assert output == expected_output

    def test_find_with_ancestors_by_id_and_bot_id(self, document_folder_seed: DocumentFolderSeed):
        # input
        root_document_folder, child_document_folders, _, bot_id = document_folder_seed
        target_document_folder = child_document_folders[0]

        want = document_folder_domain.DocumentFolderWithAncestors(
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=root_document_folder.id,
                    name=root_document_folder.name,
                    created_at=root_document_folder.created_at,
                    order=document_folder_domain.Order(root=0),
                )
            ],
            id=target_document_folder.id,
            name=target_document_folder.name,
            created_at=target_document_folder.created_at,
        )
        # execute
        got = self.document_folder_repo.find_with_ancestors_by_id_and_bot_id(
            id=target_document_folder.id, bot_id=bot_id
        )
        # assert
        assert got == want

    def test_find_with_descendants_by_id_and_bot_id(self, document_folder_seed: DocumentFolderSeed):
        # input
        (
            parent_document_folder,
            child_document_folders,
            child_child_document_folders,
            bot_id,
        ) = document_folder_seed
        target_document_folder = parent_document_folder

        want = document_folder_domain.DocumentFolderWithDescendants(
            descendant_folders=[
                document_folder_domain.DocumentFolder(
                    id=child_document_folders[0].id,
                    name=child_document_folders[0].name,
                    created_at=child_document_folders[0].created_at,
                ),
                document_folder_domain.DocumentFolder(
                    id=child_document_folders[1].id,
                    name=child_document_folders[1].name,
                    created_at=child_document_folders[1].created_at,
                ),
                document_folder_domain.DocumentFolder(
                    id=child_child_document_folders[0].id,
                    name=child_child_document_folders[0].name,
                    created_at=child_child_document_folders[0].created_at,
                ),
            ],
            id=target_document_folder.id,
            name=target_document_folder.name,
            created_at=target_document_folder.created_at,
        )
        # execute
        got = self.document_folder_repo.find_with_descendants_by_id_and_bot_id(
            id=target_document_folder.id, bot_id=bot_id
        )
        # assert
        assert got == want

    def test_find_with_descendants_by_id_and_bot_id_case_no_descendants(
        self, document_folder_seed: DocumentFolderSeed
    ):
        # input
        _, _, child_child_document_folders, bot_id = document_folder_seed
        target_document_folder = child_child_document_folders[0]

        want = document_folder_domain.DocumentFolderWithDescendants(
            descendant_folders=[],
            id=target_document_folder.id,
            name=target_document_folder.name,
            created_at=target_document_folder.created_at,
        )
        # execute
        got = self.document_folder_repo.find_with_descendants_by_id_and_bot_id(
            id=target_document_folder.id, bot_id=bot_id
        )
        # assert
        assert got == want

    def test_delete_by_bot_id(self, document_folder_seed: DocumentFolderSeed):
        _, _, _, bot_id = document_folder_seed

        self.document_folder_repo.delete_by_bot_id(bot_id)

        folders = (
            self.session.execute(
                select(DocumentFolder)
                .join(
                    DocumentFolderPath,
                    DocumentFolder.id == DocumentFolderPath.descendant_document_folder_id,
                )
                .where(DocumentFolder.bot_id == bot_id.value)
                .options(joinedload(DocumentFolder.descendants))
            )
            .unique()
            .scalars()
            .all()
        )
        assert len(folders) == 0

    @pytest.mark.parametrize("document_folder_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_bot_ids(self, document_folder_seed: DocumentFolderSeed):
        _, _, _, bot_id = document_folder_seed

        self.document_folder_repo.delete_by_bot_id(bot_id)
        self.document_folder_repo.hard_delete_by_bot_ids([bot_id])

        folders = (
            self.session.execute(
                select(DocumentFolder)
                .join(
                    DocumentFolderPath,
                    DocumentFolder.id == DocumentFolderPath.descendant_document_folder_id,
                )
                .where(DocumentFolder.bot_id == bot_id.value)
                .options(joinedload(DocumentFolder.descendants))
            )
            .unique()
            .scalars()
            .all()
        )
        assert len(folders) == 0

    @pytest.mark.parametrize("document_folder_seed", [{"cleanup_resources": False}], indirect=True)
    def test_move_document_folder(self, document_folder_seed: DocumentFolderSeed):
        # Input
        root_document_folder, child_document_folders, _, bot_id = document_folder_seed

        # target_folderをnew_parent_folderの配下に移動
        target_folder_id = child_document_folders[0].id
        new_parent_document_folder_id = child_document_folders[1].id

        # Execute
        self.document_folder_repo.move_document_folder(
            bot_id=bot_id,
            document_folder_id=target_folder_id,
            new_parent_document_folder_id=new_parent_document_folder_id,
        )

        # Assert
        moved_folder_with_ancestors = self.document_folder_repo._find_ancestors_with_order_by_id_and_bot_id(
            id=target_folder_id,
            bot_id=bot_id,
        )

        # orderとフォルダIDの両方を確認
        expected_structure = [
            (root_document_folder.id, 0),
            (new_parent_document_folder_id, 1),
            (target_folder_id, 2),
        ]
        assert [(f.id, f.order.root) for f in moved_folder_with_ancestors] == expected_structure

    @pytest.mark.parametrize("document_folder_seed", [{"cleanup_resources": False}], indirect=True)
    def test_move_document_folder_with_children(self, document_folder_seed: DocumentFolderSeed):
        # Input
        (
            root_document_folder,
            child_document_folders,
            child_child_document_folders,
            bot_id,
        ) = document_folder_seed

        # target_folderをnew_parent_folderの配下に移動
        target_folder_id = child_document_folders[0].id
        new_parent_document_folder_id = child_document_folders[1].id

        # Execute
        self.document_folder_repo.move_document_folder(
            bot_id=bot_id,
            document_folder_id=target_folder_id,
            new_parent_document_folder_id=new_parent_document_folder_id,
        )

        # Assert
        # target_folderの移動を確認
        target_folder_with_ancestors = self.document_folder_repo._find_ancestors_with_order_by_id_and_bot_id(
            id=target_folder_id,
            bot_id=bot_id,
        )

        # target_folderの祖先の階層構造を確認
        expected_source_structure = [
            (root_document_folder.id, 0),
            (new_parent_document_folder_id, 1),
            (target_folder_id, 2),
        ]
        assert [(f.id, f.order.root) for f in target_folder_with_ancestors] == expected_source_structure

        # target_folderの子フォルダの移動を確認
        child_folder_with_ancestors = self.document_folder_repo._find_ancestors_with_order_by_id_and_bot_id(
            id=child_child_document_folders[0].id,
            bot_id=bot_id,
        )

        # 子フォルダの階層構造を確認
        expected_child_structure = [
            (root_document_folder.id, 0),
            (new_parent_document_folder_id, 1),
            (target_folder_id, 2),
            (child_child_document_folders[0].id, 3),
        ]
        assert [(f.id, f.order.root) for f in child_folder_with_ancestors] == expected_child_structure

        # target_folderとその子フォルダの関係を確認
        descendants = self.document_folder_repo._find_descendants_with_order_by_id_and_bot_id(
            id=target_folder_id,
            bot_id=bot_id,
        )

        # source_folderの子フォルダが正しく移動されていることを確認
        expected_descendants = [
            (target_folder_id, 0),
            (child_child_document_folders[0].id, 1),
        ]
        assert [(f.id, f.order.root) for f in descendants] == expected_descendants
