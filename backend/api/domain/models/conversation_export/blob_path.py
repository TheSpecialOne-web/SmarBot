from pydantic import RootModel, StrictStr


class BlobPath(RootModel[StrictStr]):
    root: StrictStr
