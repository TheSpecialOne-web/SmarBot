from uuid import uuid4

from api.domain.models.search import DocumentChunk


def dummy_document_chunk(id: str, document_id: int, content: str, blob_path: str, file_name: str, file_extension: str):
    return DocumentChunk(
        id=id,
        document_id=document_id,
        bot_id=1,
        data_source_id="test",
        document_folder_id=None,
        content=content,
        blob_path=blob_path,
        file_name=file_name,
        file_extension=file_extension,
        page_number=1,
        is_vectorized=False,
        title_vector=None,
        content_vector=None,
        external_id=None,
        parent_external_id=None,
    )


class TestDocumentChunkDomain:
    def test_update_full_path_in_content(self):
        document_chunk = dummy_document_chunk(
            id=str(uuid4()),
            document_id=1,
            content="[1層目/2層目/test.pdf]:test",
            blob_path="test",
            file_name="test",
            file_extension="pdf",
        )
        document_chunk.update_full_path_in_content(full_path="1層目変更後/2層目/test.pdf")
        assert document_chunk.content == "[1層目変更後/2層目/test.pdf]:test"

        document_chunk = dummy_document_chunk(
            id=str(uuid4()),
            document_id=1,
            content="test",
            blob_path="test",
            file_name="test",
            file_extension="pdf",
        )
        document_chunk.update_full_path_in_content(full_path="1層目変更後/2層目変更後/test.pdf")
        assert document_chunk.content == "[1層目変更後/2層目変更後/test.pdf]:test"
