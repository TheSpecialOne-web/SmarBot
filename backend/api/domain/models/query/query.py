from pydantic import RootModel, StrictStr


class Query(RootModel):
    root: StrictStr


class Queries(RootModel):
    root: list[Query]

    @classmethod
    def from_list(cls, query_list: list[str]) -> "Queries":
        return Queries(root=[Query(root=query) for query in query_list])

    def __len__(self) -> int:
        return len(self.root)

    def to_string_list(self) -> list[str]:
        return [query.root for query in self.root]

    def to_string(self, delimiter: str) -> str:
        return delimiter.join(self.to_string_list())
