from pydantic import RootModel, StrictStr


class Title(RootModel):
    root: StrictStr
