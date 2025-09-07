from typing import Dict
from ..llm.base import LLMClient
from ..prompts.builder import PromptBuilder
from ..domains.models import Document
from ..util.decoders import ResponseJSONDecoder


class ResearchValueExtractor:
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder,
        decoder: ResponseJSONDecoder = ResponseJSONDecoder(),
    ) -> None:
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder
        self.decoder = decoder

    def extract(self) -> Dict[str, str]:
        prompt = self.prompt_builder.build_prompt()
        response = self.llm_client.chat(prompt)
        return self.parse_response(response)

    def parse_response(self, response: str) -> Dict[str, str]:
        return self.decoder.decode(response)
