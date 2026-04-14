import os
import json
import logging
import anthropic
from backend.llm.base import LLMProvider
from backend.pricing import MODEL_PRICING
from typing import Dict, Any, Tuple

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
        model: str = "claude-haiku-4-5-20251001",
        json_response: bool = True,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Tuple[Any, Dict[str, Any]]:
        
        if not self.client:
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "unknown"}

        self.logger.info(f"Calling Claude ({model})...")

        try:
            messages = [
                {"role": "user", "content": user_prompt}
            ]

            if max_tokens is None:
                max_tokens = 4000
                
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": messages
            }

            response = self.client.messages.create(**kwargs)
            
            content = response.content[0].text
            usage = response.usage

            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            total_tokens = input_tokens + output_tokens

            pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("claude-haiku-4-5-20251001", {"input": 0.25, "output": 1.25}))
            
            input_price = pricing.get("input", 0.0)
            output_price = pricing.get("output", 0.0)
            
            cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
            
            usage_stats = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "model": model
            }
            
            if json_response:
                import re
                try:
                    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
                    if json_match:
                        cleaned_content = json_match.group(1)
                    else:
                        first_brace = content.find('{')
                        last_brace = content.rfind('}')
                        first_bracket = content.find('[')
                        last_bracket = content.rfind(']')

                        has_obj = first_brace != -1 and last_brace != -1
                        has_arr = first_bracket != -1 and last_bracket != -1

                        if has_obj and has_arr:
                            if first_brace < first_bracket:
                                cleaned_content = content[first_brace:last_brace+1]
                            else:
                                cleaned_content = content[first_bracket:last_bracket+1]
                        elif has_obj:
                            cleaned_content = content[first_brace:last_brace+1]
                        elif has_arr:
                            cleaned_content = content[first_bracket:last_bracket+1]
                        else:
                            cleaned_content = content.strip()
                    
                    return json.loads(cleaned_content), usage_stats
                except (json.JSONDecodeError, ValueError):
                    self.logger.error(f"Failed to parse JSON: {content}")
                    return None, usage_stats
            
            return content, usage_stats

        except Exception as e:
            self.logger.error(f"Execution Error: {e}")
            return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": model}
