from pydantic import BaseModel

from api.domain.models.token import TokenCount


class TokenCountBreakdown(BaseModel):
    conversation_token_count: TokenCount
    chat_completion_token_count: TokenCount
    pdf_parser_token_count: TokenCount
    workflow_thread_token_count: TokenCount

    @property
    def total_token_count(self) -> TokenCount:
        return TokenCount(
            root=self.conversation_token_count.root
            + self.chat_completion_token_count.root
            + self.pdf_parser_token_count.root
            + self.workflow_thread_token_count.root
        )
