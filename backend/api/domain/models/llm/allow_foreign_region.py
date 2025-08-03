from pydantic import RootModel, StrictBool


class AllowForeignRegion(RootModel):
    root: StrictBool
