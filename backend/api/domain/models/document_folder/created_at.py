from datetime import datetime

from pydantic import RootModel


class CreatedAt(RootModel[datetime]):
    root: datetime

    def formatted(self) -> str:
        return self.root.strftime("%Y-%m-%dT%H:%M:%SZ")
