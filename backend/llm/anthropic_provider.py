import os
import json
import logging
import anthropic
from backend.llm.base import LLMProvider
from backend.pricing import MODEL_PRICING
from typing import Dict, Any, Tuple, Optional

class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.logger = logging.getLogger("ClaudeProvider")
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            self.logger.error("ANTHROPIC_API_KEY not found.")

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4-6",
        json_response: bool = True,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Dict[str, Any]]:

        if not self.client:
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "unknown"}

        self.logger.info(f"Calling Claude ({model})...")

        if max_tokens is None:
            max_tokens = 4000

        try:
            messages = [{"role": "user", "content": user_prompt}]

            if json_response and response_schema:
                is_wrapped = False
                if response_schema.get("type") != "object":
                    input_schema = {
                        "type": "object",
                        "properties": {
                            "result": response_schema
                        },
                        "required": ["result"]
                    }
                    is_wrapped = True
                else:
                    input_schema = response_schema

                tool_def = {
                    "name": "structured_response",
                    "description": "Return the structured response according to the schema.",
                    "input_schema": input_schema,
                }
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages,
                    tools=[tool_def],
                    tool_choice={"type": "tool", "name": "structured_response"},
                )

                usage = response.usage
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens
                total_tokens = input_tokens + output_tokens

                pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("claude-sonnet-4-6", {"input": 3.00, "output": 15.00}))
                cost = (input_tokens / 1_000_000 * pricing.get("input", 0.0)) + (output_tokens / 1_000_000 * pricing.get("output", 0.0))

                usage_stats = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "model": model,
                }

                for block in response.content:
                    if block.type == "tool_use":
                        final_input = block.input.get("result") if is_wrapped else block.input
                        return final_input, usage_stats

                self.logger.error("No tool_use block in Anthropic response")
                return None, usage_stats

            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": messages,
            }

            response = self.client.messages.create(**kwargs)

            content = response.content[0].text
            usage = response.usage

            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            total_tokens = input_tokens + output_tokens

            pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("claude-sonnet-4-6", {"input": 3.00, "output": 15.00}))
            input_price = pricing.get("input", 0.0)
            output_price = pricing.get("output", 0.0)
            cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)

            usage_stats = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "model": model,
            }

            if json_response:
                try:
                    return json.loads(content), usage_stats
                except (json.JSONDecodeError, ValueError):
                    self.logger.error(f"Failed to parse JSON: {content}")
                    return None, usage_stats

            return content, usage_stats

        except Exception as e:
            self.logger.error(f"Execution Error: {e}")
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": model}
