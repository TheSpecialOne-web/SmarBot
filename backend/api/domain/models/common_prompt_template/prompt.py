from pydantic import RootModel, StrictStr


class Prompt(RootModel):
    root: StrictStr
