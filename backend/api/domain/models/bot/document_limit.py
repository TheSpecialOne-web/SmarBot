from pydantic import RootModel, StrictInt

DEFAULT_DOCUMENT_LIMIT = 5


class DocumentLimit(RootModel):
    root: StrictInt = DEFAULT_DOCUMENT_LIMIT
