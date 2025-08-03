import pytest

from api.domain.models.search import IndexName
from api.libs.exceptions import BadRequest


class TestIndexName:
    def test_validate_value(self):
        value = ""
        assert IndexName.validate_value(value) == value

        value = "test"
        assert IndexName.validate_value(value) == value

        value = "test-bot"
        assert IndexName.validate_value(value) == value

        value = "test-bot-123"
        assert IndexName.validate_value(value) == value

    def test_validate_value_invalid(self):
        with pytest.raises(BadRequest):
            IndexName.validate_value("test-bot-123-456-789-")

        with pytest.raises(BadRequest):
            IndexName.validate_value("-test-bot-123-456-789")

        with pytest.raises(BadRequest):
            IndexName.validate_value("test-BOT-123-456-789")
