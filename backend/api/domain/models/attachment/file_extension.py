from enum import Enum
import os

from api.libs.exceptions import BadRequest
from api.libs.logging import get_logger

logger = get_logger()


class FileExtension(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"
    DOCX = "docx"
    PPTX = "pptx"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    BMP = "bmp"
    TIFF = "tiff"
    HEIF = "heif"

    @classmethod
    def from_filename(cls, filename: str) -> "FileExtension":
        try:
            _, ext = os.path.splitext(filename)
        except Exception:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイルに拡張子がありません。")
        ext_lower = ext[1:].lower()

        try:
            return cls(ext_lower)
        except Exception:
            raise BadRequest(
                f"ファイルの拡張子は {', '.join([e.value for e in FileExtension])} のいずれかである必要があります。",
            )

    def is_image(self) -> bool:
        return self in [
            FileExtension.PNG,
            FileExtension.JPEG,
            FileExtension.JPG,
            FileExtension.BMP,
            FileExtension.TIFF,
            FileExtension.HEIF,
        ]

    def is_displayable(self) -> bool:
        return self in [
            FileExtension.PDF,
            FileExtension.PNG,
            FileExtension.JPEG,
            FileExtension.JPG,
            FileExtension.BMP,
            FileExtension.TIFF,
            FileExtension.HEIF,
        ]

    def to_content_type(self) -> str:
        if self == FileExtension.PDF:
            return "application/pdf"
        if self == FileExtension.XLSX:
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if self == FileExtension.DOCX:
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if self == FileExtension.PPTX:
            return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        if self.is_image():
            return f"image/{self.value}"
        raise BadRequest("ファイルの拡張子がサポートされていません。")

    def to_pil_image_format(self) -> str:
        if self == FileExtension.JPEG or self == FileExtension.JPG:
            return "JPEG"
        if self == FileExtension.PNG:
            return "PNG"
        if self == FileExtension.BMP:
            return "BMP"
        if self == FileExtension.TIFF:
            return "TIFF"
        if self == FileExtension.HEIF:
            logger.warning("HEIF形式の画像はPILでサポートされていません。JPEG形式に変換します。")
            return "JPEG"
        raise BadRequest("ファイルの拡張子がサポートされていません。")
