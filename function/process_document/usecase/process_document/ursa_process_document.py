from uuid import UUID

from libs.feature_flag import get_feature_flag
from process_document.libs.metering import pdf_parser_metering, pdf_parser_metering_v2

from ...ai_vision.ai_vision import parse_pdf_by_azure_ai_vision
from ...blob_storage.blob_storage import BlobFile, get_files_from_blob
from ...blob_storage.blob_storage_for_ursa import (
    process_excel_files_for_ursa,
    process_excel_xls_files_for_ursa,
    process_pdf_files_for_ursa,
    process_powerpoint_files_for_ursa,
    process_word_files_for_ursa,
)
from ...cognitive_search.cognitive_search_for_ursa import upload_documents_to_index
from ...cognitive_search.cognitive_search_for_ursa_semantic import upload_hybrid_documents_to_index
from ...document_intelligence.document_intelligence import parse_pdf_by_document_intelligence
from ...libs.bot import SearchMethod
from ...libs.chunk import Chunk, convert_files_to_chunks_for_ursa
from ...libs.pdf import parse_pdf_by_pypdf
from ...llm_document_reader.llm_document_reader import parse_pdf_by_llm_document_reader
from ...postgres.postgres import Metering, Tenant, create_metering, update_document_status_to_completed
from .process_document import IProcessDocumentUseCase


class UrsaProcessDocumentUseCase(IProcessDocumentUseCase):
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
                "ai_vision": parse_pdf_by_azure_ai_vision,
                "document_intelligence": parse_pdf_by_document_intelligence,
                "llm_document_reader": parse_pdf_by_llm_document_reader,
            }.get(pdf_parser)
            if parser_func is None:
                raise Exception(f"unsupported pdf parser: {pdf_parser}")

            blob_files, page_count = process_pdf_files_for_ursa(
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
            return process_word_files_for_ursa(file_data=file_data, blob_path=blob_path)

        if file_extension == "xlsx":
            return process_excel_files_for_ursa(file_data=file_data, blob_path=blob_path)

        if file_extension == "xls":
            return process_excel_xls_files_for_ursa(file_data=file_data, blob_path=blob_path)

        if file_extension == "pptx":
            return process_powerpoint_files_for_ursa(file_data=file_data, blob_path=blob_path)

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
        # チャンク切りしなくて良いので，text_chunk_size, chunk_overlap, table_chunk_sizeは使わない
        return convert_files_to_chunks_for_ursa(uploaded_files)

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
        if search_method == SearchMethod.URSA.value:
            upload_documents_to_index(
                endpoint=endpoint,
                index_name=index_name,
                search_method=search_method,
                chunks=chunks,
                basename=basename,
                file_extension=file_extension,
                memo=memo,
                document_id=document_id,
                document_folder_id=document_folder_id,
                external_id=external_id,
                parent_external_id=parent_external_id,
            )
        elif search_method == SearchMethod.URSA_SEMANTIC.value:
            upload_hybrid_documents_to_index(
                endpoint=endpoint,
                index_name=index_name,
                search_method=search_method,
                chunks=chunks,
                basename=basename,
                file_extension=file_extension,
                memo=memo,
                document_id=document_id,
                document_folder_id=document_folder_id,
                external_id=external_id,
                parent_external_id=parent_external_id,
            )

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

    def update_document_status_to_completed(self, document_id: int) -> None:
        return update_document_status_to_completed(document_id)
