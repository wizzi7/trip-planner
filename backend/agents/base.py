from typing import Any, Dict
import os
import requests
import json
from dotenv import load_dotenv
import logging
from backend.pricing import MODEL_PRICING

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, state: Dict[str, Any] = None):
        self.name = name
        self.state = state or {}
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.logger = logging.getLogger(name)

    async def run(self, world: "WorldState", bus: "EventBus") -> Any:
        raise NotImplementedError

    def call_openrouter(self, system_prompt: str, user_prompt: str, json_response: bool = True) -> Any:
        if not self.api_key:
            self.logger.error("No API Key found.")
            return None

        self.logger.info("Calling OpenRouter...")
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "TripPlanner",
                },
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                usage_raw = data.get('usage', {})
                input_tokens = usage_raw.get('prompt_tokens', 0)
                output_tokens = usage_raw.get('completion_tokens', 0)
                total_tokens = usage_raw.get('total_tokens', 0)
                
                model_used = data.get('model', 'openai/gpt-3.5-turbo')
                pricing = MODEL_PRICING.get(model_used, MODEL_PRICING["openai/gpt-3.5-turbo"])
                
                cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
                
                usage_stats = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "model": model_used
                }
                
                if json_response:
                    content = content.replace("```json", "").replace("```", "").strip()
                    try:
                        return json.loads(content), usage_stats
                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse JSON: {content}")
                        return None, usage_stats
                return content, usage_stats
            else:
                self.logger.error(f"API Error: {response.status_code} - {response.text}")
                return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "unknown"}
                
        except Exception as e:
            self.logger.error(f"Execution Error: {e}")
            return None
