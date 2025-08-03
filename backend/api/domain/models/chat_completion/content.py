from pydantic import RootModel, StrictStr


class Content(RootModel):
    root: StrictStr
