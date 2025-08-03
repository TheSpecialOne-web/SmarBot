from pydantic import RootModel, StrictStr


class Comment(RootModel):
    root: StrictStr
