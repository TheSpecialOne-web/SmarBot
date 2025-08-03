from pydantic import RootModel, StrictStr


class BlobPath(RootModel):
    root: StrictStr
