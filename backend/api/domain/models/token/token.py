from pydantic import BaseModel, RootModel, StrictFloat, StrictInt
import tiktoken

from ..llm import ModelName


class Token(RootModel):
    root: StrictInt

    @classmethod
    def from_string(cls, value: str) -> "Token":
        MODEL_NAME = "gpt-3.5-turbo"
        encoding_model = tiktoken.encoding_for_model(MODEL_NAME)
        num_tokens = len(encoding_model.encode(value))
        return cls(root=num_tokens)

    def __iadd__(self, other: "Token") -> "Token":
        self.root += other.root
        return self


class TokenSet(BaseModel):
    query_input_token: Token
    query_output_token: Token
    response_input_token: Token
    response_output_token: Token

    def total_tokens(self) -> int:
        return (
            self.query_input_token.root
            + self.query_output_token.root
            + self.response_input_token.root
            + self.response_output_token.root
        )


class TokenCount(RootModel):
    root: StrictFloat

    @classmethod
    def from_token(cls, token: Token, model_name: ModelName, is_via_api: bool) -> "TokenCount":
        model_coefficient = model_name.get_token_coefficient(is_via_api)
        return cls(root=token.root * model_coefficient)

    def __iadd__(self, other: "TokenCount") -> "TokenCount":
        self.root += other.root
        return self
