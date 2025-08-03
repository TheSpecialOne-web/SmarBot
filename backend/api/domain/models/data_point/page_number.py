from pydantic import RootModel, StrictInt


class PageNumber(RootModel):
    root: StrictInt
