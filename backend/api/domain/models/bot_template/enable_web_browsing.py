from pydantic import RootModel, StrictBool


class EnableWebBrowsing(RootModel):
    root: StrictBool
