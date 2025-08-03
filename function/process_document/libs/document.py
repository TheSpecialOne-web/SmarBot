import base64
import re
import unicodedata


def encode_basename(basename):
    """
    basenameをNFC正規化してからbase64エンコードする関数

    :param basename: ファイル名
    :type basename: str
    :return: NFC正規化してからbase64エンコードされたbasename
    :rtype: str
    """
    basename_NFC = unicodedata.normalize("NFC", basename)
    basename_encoded = base64.urlsafe_b64encode(basename_NFC.encode()).decode("utf-8")[:-2]
    return basename_encoded


def extract_number(page_number: str) -> int:
    """
    変数名から数字を抽出する関数．

    :param var_name: 変数名
    :type var_name: str
    :return: 抽出された数字
    :rtype: int
    """
    try:
        return int(page_number)
    except ValueError:
        pass

    # 英字と数字の部分を分離する正規表現
    pattern = r"(\D+)(\d+)"
    match = re.match(pattern, page_number)

    if match:
        numbers = match.group(2)
        return int(numbers)
    raise ValueError(f"page_number: {page_number} is not matched with pattern: {pattern}")


def decode_file(file: bytes) -> str:
    ENCODING_TYPES = ["utf-8", "shift-jis", "cp932", "euc-jp"]
    decoded_text = None
    for encoding_type in ENCODING_TYPES:
        try:
            decoded_text = file.decode(encoding_type)
            break
        except UnicodeDecodeError:
            continue
    if decoded_text is None:
        raise ValueError("Invalid encoding type.")
    return decoded_text
