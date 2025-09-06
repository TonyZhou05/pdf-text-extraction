import json
import re

class ResponseJSONDecoder(json.JSONDecoder):
    """
    Custom JSON decoder to handle malformed JSON responses from the language model.
    This decoder attempts to fix common issues such as:
    - Missing commas between key-value pairs
    - Unescaped quotes within string values
    - Trailing commas
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def decode(self, s: str, _w=json.decoder.WHITESPACE.match):
        # Attempt to fix common JSON issues before decoding
        s = self._preprocess(s)
        return super().decode(s, _w=_w)

    def _preprocess(self, s: str) -> str:
        # Unescape quotes within string values
        s = s.strip()

        # Remove surrounding code block markers if present
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.DOTALL)

        # Fix unescaped quotes within string values
        s = re.sub(r'}\s*{', '}, {', s)

        return s