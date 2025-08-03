from pydantic import Field, RootModel, StrictInt

DEFAULT_DOCUMENT_LIMIT = 5


class DocumentLimit(RootModel):
    root: StrictInt = Field(default=DEFAULT_DOCUMENT_LIMIT, ge=0)
