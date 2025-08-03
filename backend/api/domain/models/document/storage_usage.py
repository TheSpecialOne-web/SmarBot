from pydantic import RootModel, StrictInt


class StorageUsage(RootModel):
    root: StrictInt
