from pydantic import RootModel, StrictBool


class IsPublic(RootModel):
    root: StrictBool
