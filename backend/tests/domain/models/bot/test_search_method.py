import pytest

from api.domain.models.bot import SearchMethod


class TestSearchMethod:
    def test_valid_value(self):
        sm = SearchMethod("bm25")
        assert sm.value == "bm25"
        assert sm == SearchMethod.BM25

        sm = SearchMethod("vector")
        assert sm.value == "vector"
        assert sm == SearchMethod.VECTOR

        sm = SearchMethod("hybrid")
        assert sm.value == "hybrid"
        assert sm == SearchMethod.HYBRID

        sm = SearchMethod("semantic_hybrid")
        assert sm.value == "semantic_hybrid"
        assert sm == SearchMethod.SEMANTIC_HYBRID

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            SearchMethod("nonexistent")
        with pytest.raises(ValueError):
            SearchMethod("invalid")
        with pytest.raises(ValueError):
            SearchMethod("search")
