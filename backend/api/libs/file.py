from io import StringIO
import os

import markdown
import pandas as pd


def markdown_to_excel(content: str, output_filename: str) -> None:
    html = markdown.markdown(content, extensions=["tables"])
    df = pd.read_html(StringIO(html))[0]
    df.to_excel(output_filename, index=False)


def get_file_extension_from_filename(filename: str) -> str:
    try:
        _, ext = os.path.splitext(filename)
    except Exception:
        raise ValueError("ファイル名が不正です。")
    if ext == "":
        raise ValueError("ファイルに拡張子がありません。")
    return ext


def is_xlsx(filename: str) -> bool:
    return get_file_extension_from_filename(filename) == ".xlsx"


def convert_halfwidth_to_fullwidth(text: str) -> str:
    reserved_chars = r"!*';:@&=+$,\\/?%#"
    encoded_text = ""
    for char in repr(text)[1:-1]:
        if char in reserved_chars:
            ascii_code = ord(char)
            full_width_code = ascii_code + 65248
            char = chr(full_width_code)
        encoded_text += char
    return encoded_text
