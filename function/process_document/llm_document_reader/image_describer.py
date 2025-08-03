import base64
import math
from typing import Annotated, Any, Generator

import cv2
from neollm import MyLLM
from neollm.exceptions import ContentFilterError
from neollm.types import Messages
from neollm.utils.preprocess import optimize_token
import numpy as np
from pydantic import (
    BaseModel,
    PlainSerializer,
    PlainValidator,
    RootModel,
    SerializationInfo,
    StrictStr,
    ValidationInfo,
)

TEXT_IN_IMAGE = "画像内のOCR結果"
TEXT_AROUND_IMAGE = "画像周辺にある文章"
MAX_PIXEL = 100000


def validate_ndarray(v: Any, info: ValidationInfo) -> np.ndarray:
    if isinstance(v, np.ndarray):
        ans = v
    elif isinstance(v, (list, tuple)):
        ans = np.array(v)
    else:
        raise TypeError(f"Expected numpy.ndarray, list or tuple of float, got {type(v)}")
    if ans.ndim != 3:
        raise ValueError(f"Expected 3D array, got {ans.ndim}D array")
    return ans


def serialize_ndarray(v: np.ndarray, info: SerializationInfo) -> list[list[float]]:
    return v.tolist()


Ndarray = Annotated[
    np.ndarray,
    PlainValidator(validate_ndarray),
    PlainSerializer(serialize_ndarray),
]


class ImageData(RootModel):
    root: Ndarray

    def _resize(self) -> "ImageData":
        vertical_pixel, horizontal_pixel = self.root.shape[:2]
        comp_rate = math.sqrt(MAX_PIXEL / (vertical_pixel * horizontal_pixel))
        if comp_rate < 1:
            self.root = cv2.resize(self.root, None, fx=comp_rate, fy=comp_rate)
        return self

    def encode_image(self) -> str:
        _, encoded_image = cv2.imencode(".png", self._resize().root)
        byte_image = encoded_image.tobytes()
        b64_encoded_image = base64.b64encode(byte_image).decode("utf-8")
        return b64_encoded_image


class ImageDescriberInput(BaseModel):
    image_data: ImageData
    text_in_image: list[StrictStr]
    text_around_image: list[StrictStr]


class ImageDescriberOutput(BaseModel):
    description: StrictStr


class ImageDescriber(MyLLM):
    def _preprocess(self, inputs: ImageDescriberInput):
        self.text_in_image = inputs.text_in_image

        system_prompt = (
            "あなたは画像説明器です。ユーザーから与えられる画像に対して適切な説明を生成して下さい。生成の際は以下の注意点を考慮して下さい。\n"
            "\n"
            "# 注意点:\n"
            "*重要* 与えられた画像内に含まれる情報を一つ残らず説明に反映させるように心がけてください。*重要*\n"
            "与えられた画像がフロー図の場合は、全ての条件分岐、パターンについて1つ1つどのような分岐を経てどのような結果に辿り着くのかを説明してください。\n"
            "与えられた画像がグラフの場合は、軸とラベルについて何を表しているかを説明したのち値の推移や大小について大まかな説明をし、最後に1つ1つの数値を読み取ってcsv形式で説明してください。\n"
            "与えられた画像が関係図の場合は、各要素がどのような関係にあるかを図中の矢印などをもとに適切に説明してください。\n"
            "- 'このグラフは'、'この図は'といった文言を説明に書く必要はありません。\n"
            f"- 与えられる<{TEXT_IN_IMAGE}>に含まれる内容を全て含めた説明を生成して下さい。\n"
            f"- 与えられる<{TEXT_AROUND_IMAGE}>に含まれる内容を適宜参照して内容を補いながら説明を生成して下さい。\n"
        )

        text_in_image_join = (
            f"<{TEXT_IN_IMAGE}>" + " ".join(text for text in inputs.text_in_image) + f"<{TEXT_IN_IMAGE}/>"
        )

        text_around_image_join = (
            f"<{TEXT_AROUND_IMAGE}>" + " ".join(text for text in inputs.text_around_image) + f"<{TEXT_AROUND_IMAGE}/>"
        )
        text_message = (
            system_prompt
            + "\n"
            + text_in_image_join
            + "\n"
            + text_around_image_join
            + "\n"
            + "それでは、回答を生成して下さい。あなたならできます。"
        )

        messages: Messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": optimize_token(text_message)},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{inputs.image_data.encode_image()}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ]
        return messages

    def _postprocess(self, response) -> ImageDescriberOutput:
        generated_text: str = response["choices"][0]["message"]["content"]

        # 画像内テキストが生成テキストに含まれていない場合、それを補足情報に追加
        text_supplement = "\n画像内に含まれる単語： "
        text_supplement += " ".join(self.text_in_image)
        generated_text += text_supplement

        text = '<img alt = "' + generated_text + '" />'
        return ImageDescriberOutput(description=text)

    def __call__(self, inputs: ImageDescriberInput) -> ImageDescriberOutput:
        """_summary_

        Args:
            inputs (ImageDescriberInput): 画像説明生成の入力(image_data, text_in_image, text_around_image)

        Raises:
            e: _description_

        Returns:
            ImageDescriberOutput: 画像説明生成の出力(description)
        """
        try:
            outputs: ImageDescriberOutput = super().__call__(inputs)
        except ContentFilterError:
            outputs = ImageDescriberOutput(description="")
        return outputs

    def call_stream(self, inputs: ImageDescriberInput) -> Generator[str, None, None]:
        """

        Args:
            inputs (ImageDescriberInput): 画像説明生成の入力(image_data, text_in_image, text_around_image)

        Raises:
            e: _description_

        Yields:
            Generator[str, None, None]: 画像説明生成の出力(ジェネレーター)
        """
        return super().call_stream(inputs)
