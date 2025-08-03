from abc import ABC, abstractmethod
from uuid import UUID

from libs.feature_flag import get_feature_flag
from libs.logging import get_logger
from process_document.libs.metering import pdf_parser_metering, pdf_parser_metering_v2

from ...ai_vision.ai_vision import parse_pdf_by_azure_ai_vision
from ...blob_storage.blob_storage import (
    BlobFile,
    get_files_from_blob,
    process_excel_files,
    process_excel_xls_files,
    process_pdf_files,
    process_powerpoint_files,
    process_text_files,
    process_word_files,
)
from ...cognitive_search.cognitive_search import upload_documents_to_tenant_index
from ...document_intelligence.document_intelligence import parse_pdf_by_document_intelligence
from ...libs.chunk import (
    Chunk,
    convert_files_to_chunk_by_html_tags,
    convert_files_to_chunks,
    convert_txt_files_to_chunks,
    split_files_to_chunks,
)
from ...libs.pdf import parse_pdf_by_pypdf
from ...llm_document_reader.llm_document_reader import parse_pdf_by_llm_document_reader
from ...postgres.postgres import Metering, Tenant, create_metering, update_document_status_to_completed

logger = get_logger(__name__)


# logger
class IProcessDocumentUseCase(ABC):
    @abstractmethod
    def get_files(
        self,
        tenant: Tenant,
        bot_id: int,
        container_name: str,
        blob_path: str,
        file_extension: str,
        pdf_parser: str,
    ) -> list[BlobFile]:
        raise NotImplementedError()

    @abstractmethod
    def convert_files_to_chunks(
        self,
        uploaded_files: list[BlobFile],
        file_extension: str,
        text_chunk_size: int | None,
        chunk_overlap: int | None,
        table_chunk_size: int | None,
        pdf_parser: str,
    ) -> list[Chunk]:
        raise NotImplementedError()

    @abstractmethod
    def upload_documents_to_index(
        self,
        endpoint: str,
        index_name: str,
        search_method: str,
        chunks: list[Chunk],
        basename: str,
        file_extension: str,
        memo: str,
        document_id: int,
        document_folder_id: UUID | None,
        external_id: str | None,
        parent_external_id: str | None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def upload_documents_to_tenant_index(
        self,
        endpoint: str,
        index_name: str,
        chunks: list[Chunk],
        bot_id: int,
        data_source_id: str,
        document_id: int,
        document_folder_id: UUID | None,
        basename: str,
        document_path: str,
        blob_path: str,
        file_extension: str,
        memo: str,
        external_id: str | None,
        parent_external_id: str | None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update_document_status_to_completed(self, document_id: int) -> None:
        raise NotImplementedError()


class ProcessDocumentUseCase(IProcessDocumentUseCase):
    def get_files(
        self,
        tenant: Tenant,
        bot_id: int,
        container_name: str,
        blob_path: str,
        file_extension: str,
        pdf_parser: str,
    ) -> list[BlobFile]:
        file_data = get_files_from_blob(container_name=container_name, blob_path=blob_path)

        if file_extension == "pdf":
            parser_func = {
                "pypdf": parse_pdf_by_pypdf,
                "document_intelligence": parse_pdf_by_document_intelligence,
                "ai_vision": parse_pdf_by_azure_ai_vision,
                "llm_document_reader": parse_pdf_by_llm_document_reader,
            }.get(pdf_parser)

            if parser_func is None:
                raise Exception(f"unsupported pdf parser: {pdf_parser}")

            blob_files, page_count = process_pdf_files(
                file_data=file_data, blob_path=blob_path, parser_func=parser_func
            )

            FLAG = "tmp-ocr-to-token"
            flag = get_feature_flag(FLAG, tenant["id"], tenant["name"])
            if flag:
                meter = pdf_parser_metering_v2(
                    tenant_id=tenant["id"], bot_id=bot_id, quantity=page_count, pdf_parser=pdf_parser
                )
            else:
                meter = pdf_parser_metering(
                    tenant_id=tenant["id"], bot_id=bot_id, quantity=page_count, pdf_parser=pdf_parser
                )

            if meter is not None:
                create_metering(
                    Metering(tenant_id=meter.tenant_id, bot_id=bot_id, type=meter.type.value, quantity=meter.quantity)
                )
            return blob_files

        if file_extension == "docx":
            return process_word_files(file_data=file_data, blob_path=blob_path)

        if file_extension == "xlsx":
            return process_excel_files(file_data=file_data, blob_path=blob_path)

        if file_extension == "xls":
            return process_excel_xls_files(file_data=file_data, blob_path=blob_path)

        if file_extension == "txt":
            return process_text_files(file_data=file_data, blob_path=blob_path)

        if file_extension == "pptx":
            return process_powerpoint_files(file_data=file_data, blob_path=blob_path)

        raise Exception(f"unsupported file format: {file_extension}")

    def convert_files_to_chunks(
        self,
        uploaded_files: list[BlobFile],
        file_extension: str,
        text_chunk_size: int | None,
        chunk_overlap: int | None,
        table_chunk_size: int | None,
        pdf_parser: str,
    ) -> list[Chunk]:
        if file_extension == "txt":
            return convert_txt_files_to_chunks(uploaded_files)
        if (
            file_extension == "pdf" and (pdf_parser == "document_intelligence" or pdf_parser == "llm_document_reader")
        ) or file_extension == "docx":
            return convert_files_to_chunk_by_html_tags(
                uploaded_files, text_chunk_size, chunk_overlap, table_chunk_size, file_extension
            )
        if file_extension == "xlsx":
            return convert_files_to_chunks(uploaded_files)
        return split_files_to_chunks(uploaded_files, text_chunk_size, chunk_overlap)

    def upload_documents_to_index(
        self,
        endpoint: str,
        index_name: str,
        search_method: str,
        chunks: list[Chunk],
        basename: str,
        file_extension: str,
        memo: str,
        document_id: int,
        document_folder_id: UUID | None,
        external_id: str | None,
        parent_external_id: str | None,
    ) -> None:
        raise NotImplementedError()

    def upload_documents_to_tenant_index(
        self,
        endpoint: str,
        index_name: str,
        chunks: list[Chunk],
        bot_id: int,
        data_source_id: str,
        document_id: int,
        document_folder_id: UUID | None,
        basename: str,
        document_path: str,
        blob_path: str,
        file_extension: str,
        memo: str,
        external_id: str | None,
        parent_external_id: str | None,
    ) -> None:
        return upload_documents_to_tenant_index(
            endpoint=endpoint,
            index_name=index_name,
            chunks=chunks,
            bot_id=bot_id,
            data_source_id=data_source_id,
            document_id=document_id,
            document_folder_id=document_folder_id,
            basename=basename,
            document_path=document_path,
            blob_path=blob_path,
            file_extension=file_extension,
            external_id=external_id,
            parent_external_id=parent_external_id,
        )

    def update_document_status_to_completed(self, document_id: int) -> None:
        return update_document_status_to_completed(document_id)
