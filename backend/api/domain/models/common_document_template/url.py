from pydantic import RootModel, StrictStr


class Url(RootModel):
    root: StrictStr
