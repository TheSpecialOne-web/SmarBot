from unittest.mock import MagicMock

from openai.types.create_embedding_response import CreateEmbeddingResponse, Usage
from openai.types.embedding import Embedding
import pytest
import tiktoken

from api.infrastructures.llm.llm import LLMService


class TestLLMService:
    @pytest.fixture
    def mock_azure_openai_client(self, monkeypatch):
        mock_client = MagicMock()
        monkeypatch.setattr("api.infrastructures.llm.llm.AOAIClient.get_azure_openai_client", mock_client)
        return mock_client

    @pytest.fixture
    def mock_tiktoken(self, monkeypatch):
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [0] * 500  # エンコード結果として適当なトークンリストを返す
        monkeypatch.setattr(tiktoken, "encoding_for_model", lambda _: mock_encoding)
        return mock_encoding

    def test_generate_embeddings_success(self, mock_azure_openai_client: MagicMock, mock_tiktoken: MagicMock):
        # サンプルの埋め込みデータを設定
        sample_embedding = [0.1, 0.2, 0.3]
        mock_response = CreateEmbeddingResponse(
            data=[Embedding(embedding=sample_embedding, index=0, object="embedding")],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=2, total_tokens=5),
        )
        mock_azure_openai_client.return_value.embeddings.create.return_value = mock_response

        # テスト実行
        text = "sample text"
        svc = LLMService(azure_credential=MagicMock())
        embeddings = svc.generate_embeddings(text)

        # 検証
        assert embeddings == sample_embedding
        mock_azure_openai_client.return_value.embeddings.create.assert_called_once_with(
            input=text, model="text-embedding-ada-002"
        )
        mock_tiktoken.encode.assert_called_once_with(text)
