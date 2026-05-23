from typing import Any, Dict, Optional
import logging
import asyncio
import time
from dotenv import load_dotenv
from backend.llm.factory import LLMFactory
from backend.llm.base import LLMProvider

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, state: Dict[str, Any] = None, llm_provider: LLMProvider = None, model_name: str = None):
        self.name = name
        self.state = state or {}
        self.logger = logging.getLogger(name)
        self.llm = llm_provider or LLMFactory.create_provider()
        self.model_name = model_name

    async def run(self, world: "WorldState", bus: "EventBus") -> Any:
        raise NotImplementedError

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        json_response: bool = True,
        model: str = None,
        max_tokens: int = None,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Any:
        target_model = model or self.model_name

        start_time = time.time()
        result = await asyncio.to_thread(
            self.llm.generate_content,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=target_model,
            json_response=json_response,
            max_tokens=max_tokens,
            response_schema=response_schema,
        )
        elapsed = round(time.time() - start_time, 3)

        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
            result[1]["latency_seconds"] = elapsed
            self.logger.info(f"LLM call completed in {elapsed}s")

        return result
