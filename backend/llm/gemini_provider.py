import os
import json
import logging
import google.genai as genai
from google.genai import types
from backend.llm.base import LLMProvider
from backend.pricing import MODEL_PRICING
from typing import Dict, Any, Tuple, Optional

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.logger = logging.getLogger("GeminiProvider")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            self.logger.error("GOOGLE_API_KEY not found.")

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gemini-3.1-pro-preview",
        json_response: bool = True,
        max_tokens: int = None,
        temperature: float = 0.7,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Dict[str, Any]]:

        if not self.client:
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "unknown"}

        self.logger.info(f"Calling Gemini ({model})...")

        try:
            config_args = {
                "temperature": temperature,
                "system_instruction": system_prompt
            }
            if max_tokens:
                config_args["max_output_tokens"] = max_tokens

            if json_response:
                config_args["response_mime_type"] = "application/json"
                if response_schema:
                    def _strip_unsupported_keys(d):
                        if isinstance(d, dict):
                            return {k: _strip_unsupported_keys(v) for k, v in d.items() if k != "additionalProperties"}
                        elif isinstance(d, list):
                            return [_strip_unsupported_keys(i) for i in d]
                        return d
                        
                    config_args["response_schema"] = _strip_unsupported_keys(response_schema)

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

                pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("gemini-3.1-pro-preview", {"input": 0, "output": 0}))
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
