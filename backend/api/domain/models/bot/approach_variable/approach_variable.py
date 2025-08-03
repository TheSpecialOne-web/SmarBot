import re

from pydantic import BaseModel, field_validator

from .name import Name
from .value import Value


class ApproachVariable(BaseModel):
    name: Name
    value: Value

    @field_validator("value")
    def check_non_negative_number(cls, v: Value):
        # Regex for matching an integer, float, or negative number
        if re.match(r"^-?\d+(\.\d+)?$", v.value):
            # Convert to float only after confirming the format, to check if it's non-negative
            numeric_value = float(v.value)
            if numeric_value < 0:
                raise ValueError("Value must be greater than or equal to 0")
        return v


class ApproachVariableList(BaseModel):
    approach_variables: list[ApproachVariable]

    def to_dict(self) -> dict[str, str]:
        """
        ApproachVariableListを辞書に変換する
        """
        approach_dict = {}
        for approach_variable in self.approach_variables:
            approach_dict[approach_variable.name.value] = approach_variable.value.value
        return approach_dict
