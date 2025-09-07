from typing import List, Dict


class LLMClient:
    def __init__(self):
        self.client = None

    def chat(self, messages: str, **kwargs) -> str:
        raise NotImplementedError
