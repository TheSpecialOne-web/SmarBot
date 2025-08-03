from pydantic import RootModel, StrictBool


class IsActive(RootModel[StrictBool]):
    root: StrictBool
