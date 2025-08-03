from pydantic import RootModel, StrictInt


class MaxConversationTurns(RootModel):
    root: StrictInt
