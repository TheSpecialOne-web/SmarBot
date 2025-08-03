from pydantic import RootModel, StrictBool


class IsBlobDeleted(RootModel):
    root: StrictBool
