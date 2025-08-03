from pydantic import RootModel, StrictStr


# e.g. "/external_root_folder/connectiong_folder/subfolder/subfolder/test.pdf"
# 外部データ内での絶対パス。連携先のフォルダ(connectiong_folder)より上のパスを含む。
class ExternalFullPath(RootModel):
    root: StrictStr
