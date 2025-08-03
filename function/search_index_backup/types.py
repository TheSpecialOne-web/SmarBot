from typing import Optional

from pydantic import BaseModel


class SortField(BaseModel):
    key: str
    value: str | None


class IndexBackupQueue(BaseModel):
    datetime: str
    endpoint: str
    index_name: str
    sort_field_value: Optional[str] = None
