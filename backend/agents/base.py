from typing import Any, Dict
import os
import json
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv
import logging
from backend.pricing import MODEL_PRICING

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, state: Dict[str, Any] = None):
        self.name = name
        self.state = state or {}
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.logger = logging.getLogger(name)
        self.client = genai.Client(api_key=self.api_key)

    async def run(self, world: "WorldState", bus: "EventBus") -> Any:
        raise NotImplementedError

    def call_gemini(self, system_prompt: str, user_prompt: str, json_response: bool = True, model: str = "gemini-2.5-flash", max_tokens: int = None) -> Any:
        if not self.client:
            self.logger.error("No Google API Key found or Client not initialized.")
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "unknown"}

        self.logger.info(f"Calling Gemini ({model})...")
        
        try:
            config_args = {
                "temperature": 0.7,
                "system_instruction": system_prompt
            }
            if max_tokens:
                config_args["max_output_tokens"] = max_tokens
            
            if json_response:
                config_args["response_mime_type"] = "application/json"

            response = self.client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(**config_args)
            )
            
            if response.text:
                content = response.text
                usage = response.usage_metadata

                input_tokens = usage.prompt_token_count if usage else 0
                output_tokens = usage.candidates_token_count if usage else 0
                total_tokens = usage.total_token_count if usage else 0
                
                pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-2.5-flash"])
                cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
                
                usage_stats = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "model": model
                }
                
                if json_response:
                     try:
                        return json.loads(content), usage_stats
                     except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse JSON: {content}")
                        return None, usage_stats
                
                return content, usage_stats
            else:
                self.logger.error("Empty response from Gemini")
                return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": model}

        except Exception as e:
            self.logger.error(f"Execution Error: {e}")
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": model}
