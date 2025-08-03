from typing import Optional

from pydantic import BaseModel

from ..document import (
    FileExtension as DocumentFileExtension,
    Id as DocumentId,
    Name as DocumentName,
)
from ..document_folder import DocumentFolderWithOrder
from ..question_answer.answer import Answer
from ..question_answer.id import Id as QuestionAnswerId
from ..question_answer.question import Question
from .additional_info import AdditionalInfo
from .blob_path import BlobPath
from .chunk_name import ChunkName
from .cite_number import CiteNumber
from .content import Content
from .page_number import PageNumber
from .type import Type
from .url import Url


class DataPointWithoutCiteNumber(BaseModel):
    content: Content
    page_number: PageNumber
    chunk_name: ChunkName
    blob_path: BlobPath
    type: Type
    url: Url
    document_id: Optional[DocumentId] = None
    question_answer_id: Optional[QuestionAnswerId] = None
    additional_info: Optional[AdditionalInfo] = None


class DataPoint(DataPointWithoutCiteNumber):
    cite_number: CiteNumber


class DataPointWithDetail(DataPoint):
    document_name: Optional[DocumentName] = None
    document_file_extension: Optional[DocumentFileExtension] = None
    document_folders: Optional[list[DocumentFolderWithOrder]] = None
    question: Optional[Question] = None
    answer: Optional[Answer] = None
