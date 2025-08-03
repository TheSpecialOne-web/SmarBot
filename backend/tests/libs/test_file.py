import os

import pandas as pd

from api.libs.file import markdown_to_excel


class TestFile:
    def test_markdown_to_excel(self):
        content = """
| col1 | col2 | col3 |
|:---:|:---|---|
| a | b | c |
| d | e | f |
"""
        output_filename = "output.xlsx"
        markdown_to_excel(content, output_filename)
        df = pd.read_excel(output_filename)
        assert df.equals(pd.DataFrame({"col1": ["a", "d"], "col2": ["b", "e"], "col3": ["c", "f"]}))
        os.remove(output_filename)
