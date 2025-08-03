from pydantic import RootModel, StrictInt


class Order(RootModel):
    root: StrictInt
