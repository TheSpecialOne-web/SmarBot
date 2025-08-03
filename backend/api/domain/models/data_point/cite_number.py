from pydantic import RootModel, StrictInt


class CiteNumber(RootModel):
    root: StrictInt
