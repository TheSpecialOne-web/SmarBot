from pydantic import RootModel, StrictInt


class Quantity(RootModel):
    root: StrictInt
