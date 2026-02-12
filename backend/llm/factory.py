from backend.llm.base import LLMProvider
from backend.llm.gemini_provider import GeminiProvider
from backend.llm.openai_provider import OpenAIProvider
from backend.llm.anthropic_provider import AnthropicProvider

class LLMFactory:
    @staticmethod
    def create_provider(provider: str = "gemini") -> LLMProvider:
        provider_type = provider.lower()
        
        if provider_type == "openai":
            return OpenAIProvider()
        elif provider_type in ["claude", "anthropic"]:
            return AnthropicProvider()
        else:
            return GeminiProvider()
