import os
import json
import logging
from typing import Dict, Any, Tuple, Optional
from backend.llm.base import LLMProvider
import openai

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.logger = logging.getLogger("OpenAIProvider")
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            self.logger.error("OPENAI_API_KEY not found.")

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o",
        json_response: bool = True,
        max_tokens: int = None,
        temperature: float = 1,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Dict[str, Any]]:

        if not self.client:
             return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "unknown"}

        self.logger.info(f"Calling OpenAI ({model})...")

        _unwrap_array = False
        if response_schema and response_schema.get("type") == "array":
            wrapped_schema = {
                "type": "object",
                "properties": {"items": response_schema},
                "required": ["items"],
                "additionalProperties": False,
            }
            _unwrap_array = True
        else:
            wrapped_schema = response_schema

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                kwargs["max_completion_tokens"] = max_tokens

            if json_response:
                if wrapped_schema:
                    kwargs["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "structured_response",
                            "strict": True,
                            "schema": wrapped_schema,
                        },
                    }
                else:
                    kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content
            usage = response.usage

            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            pricing_map = {
                "gpt-4o": {"input": 5.0, "output": 15.0},
                "gpt-4o-2024-05-13": {"input": 5.0, "output": 15.0},
                "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
                "gpt-4o-mini": {"input": 0.15, "output": 0.60},
                "gpt-5.4": {"input": 0.15, "output": 0.60},
                "unknown": {"input": 0, "output": 0}
            }

            pricing = pricing_map.get(model, pricing_map.get("gpt-3.5-turbo"))
            cost = (input_tokens / 1_000_000 * pricing.get("input", 0)) + (output_tokens / 1_000_000 * pricing.get("output", 0))

            usage_stats = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "model": model
            }

            if json_response:
                try:
                    parsed = json.loads(content)
                    if _unwrap_array and isinstance(parsed, dict) and "items" in parsed:
                        parsed = parsed["items"]
                    return parsed, usage_stats
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse JSON: {content}")
                    return None, usage_stats

            return content, usage_stats

        except Exception as e:
            self.logger.error(f"Execution Error: {e}")
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": model}
