from pydantic import RootModel, StrictBool


class UseWebBrowsing(RootModel):
    root: StrictBool
