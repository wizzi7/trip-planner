from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class LLMProvider(ABC):
    @abstractmethod
    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        json_response: bool = True,
        max_tokens: int = None,
        temperature: float = 0.7
    ) -> Tuple[Any, Dict[str, Any]]:
        pass
