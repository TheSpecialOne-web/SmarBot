from enum import Enum


class SearchMethod(Enum):
    """
    検索方法を表すEnum
    """

    BM25 = "bm25"
    VECTOR = "vector"
    HYBRID = "hybrid"
    # TODO コメントアウト部分の検索メソッドを作成する
    # BM25_HYBRID = "bm25_hybrid"
    # VECTOR_HYBRID = "vector_hybrid"
    SEMANTIC_HYBRID = "semantic_hybrid"
    URSA = "ursa"
    URSA_SEMANTIC = "ursa_semantic"

    def should_create_embeddings(self) -> bool:
        """
        埋め込みを作成するかどうかを返す
        """
        return self in [
            SearchMethod.BM25,
            SearchMethod.VECTOR,
            SearchMethod.HYBRID,
            SearchMethod.SEMANTIC_HYBRID,
        ]

    @classmethod
    # valueがEnumに含まれているかどうかを返す
    def has_value(cls, value):
        return any(value == item.value for item in cls)
