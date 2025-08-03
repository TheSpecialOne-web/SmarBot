from pydantic import RootModel, StrictStr


class Message(RootModel):
    root: StrictStr
