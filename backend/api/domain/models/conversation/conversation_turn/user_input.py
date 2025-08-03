from typing import Tuple

from pydantic import RootModel, StrictStr

from api.domain.models.conversation.validation import SensitiveContentType


class UserInput(RootModel):
    root: StrictStr

    def check_sensitive_contents(self, content_type: SensitiveContentType) -> Tuple[bool, str]:
        pattern = SensitiveContentType.get_pattern(content_type)
        if pattern is None:
            raise ValueError(f"Invalid sensitive content type: {content_type}")
        sensitive_contents = pattern.findall(self.root)
        if len(sensitive_contents) != 0:
            matches = ""
            for i, sensitive_content in enumerate(sensitive_contents):
                if i != 0:
                    matches += ", "
                matches += sensitive_content
            return True, matches
        return False, ""
