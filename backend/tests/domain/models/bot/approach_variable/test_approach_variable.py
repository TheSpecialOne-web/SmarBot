import pytest  # noqa

from api.domain.models.bot.approach_variable import (
    ApproachVariable,
    ApproachVariableList,
    Name,
    Value,
)


class TestApproachVariableList:
    def test_to_dict(self):
        approach_variable_list = ApproachVariableList(
            approach_variables=[
                ApproachVariable(name=Name(value="test_name"), value=Value(value="test_value")),
                ApproachVariable(name=Name(value="test_name_2"), value=Value(value="test_value_2")),
            ]
        )

        assert approach_variable_list.to_dict() == {
            "test_name": "test_value",
            "test_name_2": "test_value_2",
        }
