from backend.llm.factory import LLMFactory
from backend.llm.gemini_provider import GeminiProvider
from backend.llm.openai_provider import OpenAIProvider
from backend.llm.anthropic_provider import AnthropicProvider


class TestLLMFactory:
    def test_default_is_gemini(self):
        provider = LLMFactory.create_provider()
        assert isinstance(provider, GeminiProvider)

    def test_gemini_explicit(self):
        provider = LLMFactory.create_provider("gemini")
        assert isinstance(provider, GeminiProvider)

    def test_openai(self):
        provider = LLMFactory.create_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_claude(self):
        provider = LLMFactory.create_provider("claude")
        assert isinstance(provider, AnthropicProvider)

    def test_anthropic_alias(self):
        provider = LLMFactory.create_provider("anthropic")
        assert isinstance(provider, AnthropicProvider)

    def test_case_insensitive_openai(self):
        provider = LLMFactory.create_provider("OpenAI")
        assert isinstance(provider, OpenAIProvider)

    def test_case_insensitive_claude(self):
        provider = LLMFactory.create_provider("Claude")
        assert isinstance(provider, AnthropicProvider)

    def test_unknown_defaults_to_gemini(self):
        provider = LLMFactory.create_provider("unknown_provider")
        assert isinstance(provider, GeminiProvider)
