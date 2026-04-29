import pytest
from backend.models import UserInput

class FakeLLMProvider:
    def __init__(self, response_data=None):
        self.response_data = response_data
        self.calls = []

    def generate_content(self, system_prompt, user_prompt, **kwargs):
        self.calls.append({
            "system": system_prompt,
            "user": user_prompt,
            "kwargs": kwargs,
        })
        usage = {
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "cost": 0.001,
            "model": "fake-model",
        }
        return self.response_data, usage


@pytest.fixture
def sample_user_input():
    return UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro", "bus"],
    )


@pytest.fixture
def fake_llm():
    return FakeLLMProvider()
