import os
from research_extractor.llm.azure import AzureOpenAIClient
from typing import Dict, Any

class TableAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key is missing. Pass it to init or set OPENAI_API_KEY env var.")
        
        self.client = AzureOpenAIClient()

    def analyze(self, raw_string: str, user_prompt: str) -> str:
        """
        Sends the base64 encoded table to GPT-4o for analysis.
        """
        if not raw_string:
            raise ValueError("No raw string found")
        
        data_url = f"data:image/jpeg;base64,{raw_string}"

        # 4. Make the API Call
        try:
            response = self.client.chat(
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a specialized clinical research assistant. Extract data accurately from medical tables. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url,
                                    "detail": "high" # Forces high-res processing for small text
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            return response
            
        except Exception as e:
            return f"Error during OpenAI inference: {str(e)}"