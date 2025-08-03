from pydantic import BaseModel

from api.domain.models.document import Document
from api.domain.models.user import Name as UserName


class DocumentWithCreator(Document):
    creator_name: UserName | None


class GetDocumentsOutput(BaseModel):
    documents: list[DocumentWithCreator]
