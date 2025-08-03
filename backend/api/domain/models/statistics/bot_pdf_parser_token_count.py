from typing import TypedDict

from pydantic import BaseModel

from ..bot import Id, Name
from ..metering import BotPdfParserPageCount
from ..token import TokenCount


class BotPdfParserTokenCount(BaseModel):
    bot_id: Id
    bot_name: Name
    token_count: TokenCount

    @classmethod
    def from_bot_pdf_parser_page_count(
        cls, bot_pdf_parser_page_count: BotPdfParserPageCount
    ) -> "BotPdfParserTokenCount":
        return cls(
            bot_id=bot_pdf_parser_page_count.bot_id,
            bot_name=bot_pdf_parser_page_count.bot_name,
            token_count=TokenCount(
                root=bot_pdf_parser_page_count.page_count.root
                * bot_pdf_parser_page_count.count_type.get_token_count_coefficient()
            ),
        )


class BotPdfParserTokenCountSummary(BaseModel):
    total_count: TokenCount
    bot_pdf_parsers_tokens: list[BotPdfParserTokenCount]

    @classmethod
    def from_list_bot_pdf_parser_token_count(
        cls, bot_pdf_parsers_token_counts: list[BotPdfParserTokenCount]
    ) -> "BotPdfParserTokenCountSummary":
        class BotData(TypedDict):
            bot_name: str
            token_count: float

        grouped_counts: dict[int, BotData] = {}

        # bot_id ごとに token_count を合計
        for token_count in bot_pdf_parsers_token_counts:
            if token_count.bot_id.value in grouped_counts:
                grouped_counts[token_count.bot_id.value]["token_count"] += token_count.token_count.root
            else:
                grouped_counts[token_count.bot_id.value] = {
                    "bot_name": token_count.bot_name.value,
                    "token_count": token_count.token_count.root,
                }

        # 合計された BotPdfParserTokenCount インスタンスのリストを作成
        bot_pdf_parsers_token_counts = [
            BotPdfParserTokenCount(
                bot_id=Id(value=bot_id),
                bot_name=Name(value=data["bot_name"]),
                token_count=TokenCount(root=data["token_count"]),
            )
            for bot_id, data in grouped_counts.items()
        ]

        bot_pdf_parsers_token_counts.sort(
            key=lambda bot_pdf_parsers_token_count: bot_pdf_parsers_token_count.token_count.root, reverse=True
        )

        # 総トークン数を計算
        total_count = TokenCount(
            root=sum(
                bot_pdf_parsers_token_count.token_count.root
                for bot_pdf_parsers_token_count in bot_pdf_parsers_token_counts
            )
        )

        return cls(total_count=total_count, bot_pdf_parsers_tokens=bot_pdf_parsers_token_counts)
