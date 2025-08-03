import pytest

from api.domain.models.storage import ContainerName
from api.libs.exceptions import BadRequest


class TestContainerName:
    def test_validate_value(self):
        value = ""
        assert ContainerName.validate_value(value) == value

        value = "test"
        assert ContainerName.validate_value(value) == value

        value = "test-bot"
        assert ContainerName.validate_value(value) == value

        value = "test-bot-123"
        assert ContainerName.validate_value(value) == value

    def test_validate_value_invalid(self):
        with pytest.raises(BadRequest):
            ContainerName.validate_value("test-bot-123-456-789-")

        with pytest.raises(BadRequest):
            ContainerName.validate_value("-test-bot-123-456-789")

        with pytest.raises(BadRequest):
            ContainerName.validate_value("test-BOT-123-456-789")
