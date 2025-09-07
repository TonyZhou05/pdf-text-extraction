from openai import OpenAI
from .base import LLMClient
import os
import dotenv

dotenv.load_dotenv()


class OpenAIClient(LLMClient):
    def __init__(self, model: str = "gpt-4o") -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def chat(self, messages: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": messages}], **kwargs
        )
        return response.choices[0].message.content.strip()
