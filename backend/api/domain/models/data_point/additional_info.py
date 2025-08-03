from typing import Any

from pydantic import RootModel


class AdditionalInfo(RootModel):
    root: dict[str, Any]
