from pydantic import RootModel, StrictStr


class ImageUrl(RootModel):
    root: StrictStr = ""

    def to_markdown(self):
        return f"![image]({self.root})"
