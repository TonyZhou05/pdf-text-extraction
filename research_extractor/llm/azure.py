from openai import AzureOpenAI
from .base import LLMClient
import os
import dotenv

dotenv.load_dotenv()


class AzureOpenAIClient(LLMClient):
    def __init__(self, model: str = "gpt-4o") -> None:
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            azure_ad_token=os.getenv("AZURE_OPENAI_AD_TOKEN", None),
            # to be replaced with env variable
            api_version="2024-02-15-preview",
        )
        self.model = model

    def chat(self, messages, **kwargs) -> str:
        """
        Accept either a plain string prompt or a fully-formed messages list.
        This is required for multimodal requests (text + image) used by the table analyzer.
        """
        payload = (
            [{"role": "user", "content": messages}]
            if isinstance(messages, str)
            else messages
        )

        response = self.client.chat.completions.create(
            model=self.model, messages=payload, **kwargs
        )
        return response.choices[0].message.content.strip()
