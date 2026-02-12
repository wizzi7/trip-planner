from backend.llm.base import LLMProvider
from backend.llm.gemini_provider import GeminiProvider
from backend.llm.openai_provider import OpenAIProvider

class LLMFactory:
    @staticmethod
    def create_provider(provider: str = "gemini") -> LLMProvider:
        provider_type = provider.lower()
        
        if provider_type == "openai":
            return OpenAIProvider()
        else:
            return GeminiProvider()
