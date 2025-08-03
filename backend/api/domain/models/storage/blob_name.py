from pydantic import RootModel, StrictStr


class BlobName(RootModel):
    root: StrictStr
