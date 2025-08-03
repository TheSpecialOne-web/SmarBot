from pydantic import RootModel, StrictStr


class Name(RootModel):
    root: StrictStr
