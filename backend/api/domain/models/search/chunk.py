from datetime import datetime, timezone
import uuid

from pydantic import BaseModel, Field, StrictFloat, StrictInt, StrictStr

FLOAT_SIZE = 4
INT_SIZE = 4


def _create_uuid() -> str:
    return str(uuid.uuid4())


def _create_datetime_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DocumentChunk(BaseModel):
    id: StrictStr = Field(default_factory=_create_uuid)
    bot_id: StrictInt
    data_source_id: StrictStr
    document_id: StrictInt
    document_folder_id: StrictStr | None
    content: StrictStr
    blob_path: StrictStr
    file_name: StrictStr
    file_extension: StrictStr
    page_number: StrictInt
    created_at: StrictStr = Field(default_factory=_create_datetime_now)
    updated_at: StrictStr = Field(default_factory=_create_datetime_now)
    is_vectorized: bool
    title_vector: list[StrictFloat] | None
    content_vector: list[StrictFloat] | None
    external_id: StrictStr | None
    parent_external_id: StrictStr | None

    def update_blob_path(self, blob_path: StrictStr) -> None:
        self.blob_path = blob_path

    def update_file_name(self, file_name: StrictStr) -> None:
        self.file_name = file_name

    def update_updated_at(self) -> None:
        self.updated_at = _create_datetime_now()

    def update_is_vectorized_true(self) -> None:
        self.is_vectorized = True

    def update_is_vectorized_false(self) -> None:
        self.is_vectorized = False

    def add_title_vector(self, title_vector: list[StrictFloat]) -> None:
        self.title_vector = title_vector

    def add_content_vector(self, content_vector: list[StrictFloat]) -> None:
        self.content_vector = content_vector

    def update_document_folder_id(self, document_folder_id: StrictStr) -> None:
        self.document_folder_id = document_folder_id

    def update_full_path_in_content(self, full_path: str) -> None:
        # NOTE: some_str.replace("", replacement, 1) is equivalent to f"{replacement}{some_str}"
        self.content = self.content.replace(self.content_prefix, f"[{full_path}]:", 1)

    # e.g. "[path/to/folder/file_name]:"
    @property
    def content_prefix(self) -> str:
        has_brackets = self.content.startswith("[") and "]:" in self.content
        if not has_brackets:
            return ""
        return self.content[: self.content.index("]:") + 2]

    @property
    def content_without_folder_path(self) -> str:
        content_prefix = self.content_prefix
        if content_prefix == "":
            return self.content
        return self.content.replace(content_prefix, f"[{self.file_name}]:", 1)

    @property
    def storage_usage(self) -> int:
        storage_usage = 0
        for value in self.model_dump().values():
            if isinstance(value, str):
                storage_usage += len(value.encode("utf-8"))
            elif isinstance(value, int):
                storage_usage += INT_SIZE
            elif isinstance(value, list):
                # ref: https://learn.microsoft.com/en-us/azure/search/vector-search-index-size?tabs=portal-vector-quota
                # "the disk consumption for vector data is roughly three times the size of the vector index in memory."
                storage_usage += len(value) * FLOAT_SIZE * 3
        return storage_usage


class UrsaDocumentChunk(BaseModel):
    id: StrictStr = Field(default_factory=_create_uuid)
    content: StrictStr
    file_name: StrictStr
    construction_name: StrictStr
    author: StrictStr
    year: StrictInt
    branch: StrictStr
    document_type: StrictStr
    interpolation_path: StrictStr
    full_path: StrictStr
    extension: StrictStr
    source_file: StrictStr | None
    created_at: StrictStr = Field(default_factory=_create_datetime_now)
    updated_at: StrictStr = Field(default_factory=_create_datetime_now)
    sourceid: StrictStr
    document_id: StrictInt
    document_folder_id: StrictStr | None
    external_id: StrictStr | None
    parent_external_id: StrictStr | None

    def update_file_name(self, file_name: StrictStr) -> None:
        self.file_name = file_name + "." + self.extension

    def update_full_path(self, memo: StrictStr) -> None:
        self.full_path = memo

    def update_document_folder_id(self, document_folder_id: StrictStr) -> None:
        self.document_folder_id = document_folder_id

    def update_updated_at(self) -> None:
        self.updated_at = _create_datetime_now()

    def update_param_from_full_path(self, full_path: StrictStr) -> None:
        self.full_path = full_path
        # TODO: @ursa 実装
