from pydantic import RootModel, StrictInt


class Step(RootModel[StrictInt]):
    root: StrictInt
