from typing import Any, Dict
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, state: Dict[str, Any] = None):
        self.name = name
        self.state = state or {}
        self.api_key = os.environ.get("OPENROUTER_API_KEY")

    async def run(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def call_openrouter(self, system_prompt: str, user_prompt: str, json_response: bool = True) -> Any:
        if not self.api_key:
            print(f"[{self.name}] ERROR: No API Key found.")
            return None

        print(f"[{self.name}] Calling OpenRouter...")
        
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
                
                if json_response:
                    content = content.replace("```json", "").replace("```", "").strip()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        print(f"[{self.name}] Failed to parse JSON: {content}")
                        return None
                return content
            else:
                print(f"[{self.name}] API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[{self.name}] Execution Error: {e}")
            return None
