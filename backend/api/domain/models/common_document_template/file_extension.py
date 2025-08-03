from enum import Enum
import os

from api.libs.exceptions import BadRequest


class FileExtension(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"

    @classmethod
    def from_filename(cls, filename: str) -> "FileExtension":
        try:
            _, ext = os.path.splitext(filename)
        except Exception:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイルの拡張子が取得できません。")
        ext_lower = ext[1:].lower()

        try:
            return cls(ext_lower)
        except Exception:
            raise BadRequest(
                f"ファイルの拡張子は {', '.join([e.value for e in FileExtension])} のいずれかである必要があります。",
            )

    def to_content_type(self) -> str:
        return {
            FileExtension.PDF: "application/pdf",
            FileExtension.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            FileExtension.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            FileExtension.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            FileExtension.TXT: "text/plain; charset=utf-8",
        }[self]

    def is_convertible_to_pdf(self) -> bool:
        """PDFへ変換されるべきファイルタイプかどうかを返す。

        Returns:
            bool: 変換されるべき場合は True、それ以外の場合は False。
        """
        return self in [
            FileExtension.DOCX,
            FileExtension.XLSX,
            FileExtension.PPTX,
        ]
