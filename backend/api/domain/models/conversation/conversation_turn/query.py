from pydantic import RootModel, StrictStr


class Query(RootModel):
    root: StrictStr

    def shortened(self, max_length: int) -> "Query":
        if len(self.root) > max_length:
            return Query(root=self.root[:max_length])
        return self
