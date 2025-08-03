import re

from pydantic import RootModel, StrictStr


class Content(RootModel):
    root: StrictStr

    def remove_citations(self):
        self.root = re.sub(r"\[\d+\]\((?:cite:\d+)?\)", "", self.root)

    def remove_bold(self):
        self.root = re.sub(r"\*\*(.*?)\*\*", r"\1", self.root)
