from backend.pricing import MODEL_PRICING


class TestModelPricing:
    def test_not_empty(self):
        assert len(MODEL_PRICING) > 0

    def test_all_models_have_input_and_output(self):
        for model, prices in MODEL_PRICING.items():
            assert "input" in prices, f"{model} missing 'input' pricing"
            assert "output" in prices, f"{model} missing 'output' pricing"

    def test_all_prices_non_negative(self):
        for model, prices in MODEL_PRICING.items():
            assert prices["input"] >= 0, f"{model} has negative input price"
            assert prices["output"] >= 0, f"{model} has negative output price"

    def test_all_prices_are_numeric(self):
        for model, prices in MODEL_PRICING.items():
            assert isinstance(prices["input"], (int, float)), f"{model} input is not numeric"
            assert isinstance(prices["output"], (int, float)), f"{model} output is not numeric"

    def test_known_gemini_model_exists(self):
        assert "gemini-3.1-pro-preview" in MODEL_PRICING

    def test_known_openai_model_exists(self):
        assert "gpt-4o" in MODEL_PRICING

    def test_known_anthropic_model_exists(self):
        assert "claude-sonnet-4-6" in MODEL_PRICING

    def test_output_price_gte_input_price(self):
        for model, prices in MODEL_PRICING.items():
            assert prices["output"] >= prices["input"], (
                f"{model}: output price ({prices['output']}) < input price ({prices['input']})"
            )
