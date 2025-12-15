import os
import json
from research_extractor.llm.azure import AzureOpenAIClient
from typing import Dict, Any

class TableAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key is missing. Pass it to init or set OPENAI_API_KEY env var.")
        
        self.client = AzureOpenAIClient()

    def analyze(self, raw_string: str, user_prompt: str) -> Dict[str, Any]:
        if not raw_string:
            return {}
        
        data_url = f"data:image/jpeg;base64,{raw_string}"

        try:
            response = self.client.chat(
                messages=[
                    {
                        "role": "system", 
                        # CRITICAL: You must mention 'JSON' in the prompt for JSON mode to work
                        "content": "You are a clinical assistant. Output JSON only."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}}
                        ]
                    }
                ],
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            print(response)
            
            # Now it is safe to load directly
            return response
            
        except Exception as e:
            print(f"Error: {e}")
            # Fallback structure so your pipeline doesn't crash
            return {"metadata": {"keywords": [], "title": "Error"}, "html": ""}