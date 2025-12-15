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
        final_results = {
            "result": [],
            "treatments": []
        }

        categories = ["metadata", "demographics", "treatments"]

        print(f"Starting batched extraction for {len(categories)} categories...")

        for category in categories:
            print(f"--- Processing Batch: {category.upper()} ---")

            try:
                prompt = self.prompt_builder.build_prompt(category=category)
                response_str = self.llm_client.chat(prompt)
                
                parsed_data = self.parse_response(response_str)

                if category == "treatments":
                    treatments = parsed_data.get("treatments", [])
                    final_results["treatments"].extend(treatments)
                else:
                    result = parsed_data.get("result", [])
                    final_results["result"].extend(result)

            except Exception as e:
                print(f"Debug: Error processing batch '{category}': {e}")
                continue

        return final_results

    def parse_response(self, response: str) -> Dict[str, str]:
        return self.decoder.decode(response)
