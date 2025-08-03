import os

from pydantic import RootModel, StrictStr

AZURE_PUBLIC_STORAGE_ACCOUNT = os.environ.get("AZURE_PUBLIC_STORAGE_ACCOUNT")
AZURE_FRONT_DOOR_PUBLIC_STORAGE_ENDPOINT = os.environ.get("AZURE_FRONT_DOOR_PUBLIC_STORAGE_ENDPOINT")


class IconUrl(RootModel):
    root: StrictStr

    def replace_base_url(self) -> StrictStr:
        return self.root.replace(
            f"https://{AZURE_PUBLIC_STORAGE_ACCOUNT}.blob.core.windows.net/",
            f"{AZURE_FRONT_DOOR_PUBLIC_STORAGE_ENDPOINT}/",
        )
