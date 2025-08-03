from pydantic import RootModel, StrictStr


class BotOutput(RootModel):
    root: StrictStr
