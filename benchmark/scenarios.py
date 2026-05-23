"""
Benchmark test scenarios for LLM model comparison.
3 scenarios × 3 models × 3 repetitions = 27 experiment runs.
"""

SCENARIOS = [
    {
        "id": "S1_warszawa",
        "label": "Warszawa — krótki wyjazd, tempo relaksacyjne",
        "params": {
            "destination": "Warszawa, Polska",
            "arrival": "2026-06-13 08:00",
            "departure": "2026-06-14 22:00",
            "guests": 2,
            "budget": 600.0,
            "pace": "relaxed",
            "transport": ["public_transport"],
            "interests": ["street art", "local cuisine", "nightlife"],
            "extra_req": None,
        },
    },
    {
        "id": "S2_ateny",
        "label": "Ateny — intensywne zwiedzanie, destynacja śródziemnomorska",
        "params": {
            "destination": "Athens, Greece",
            "arrival": "2026-05-07 23:00",
            "departure": "2026-05-11 07:00",
            "guests": 2,
            "budget": 1500.0,
            "pace": "intensive",
            "transport": ["walking"],
            "interests": ["ancient ruins", "mythology", "photography"],
            "extra_req": None,
        },
    },
    {
        "id": "S3_londyn",
        "label": "Londyn — większa grupa, wysoki budżet, umiarkowane tempo",
        "params": {
            "destination": "London, United Kingdom",
            "arrival": "2026-09-10 12:00",
            "departure": "2026-09-13 16:00",
            "guests": 3,
            "budget": 4000.0,
            "pace": "moderate",
            "transport": ["public_transport", "taxi"],
            "interests": ["theatre", "shopping", "gastronomy"],
            "extra_req": None,
        },
    },
]

MODELS = [
    {
        "id": "gemini",
        "provider": "gemini",
        "model": "gemini-3.5-flash",
        "label": "Gemini 3.5 Flash (Google)",
    },
    {
        "id": "gpt54",
        "provider": "openai",
        "model": "gpt-5.4",
        "label": "GPT-5.4 (OpenAI)",
    },
    {
        "id": "claude",
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "label": "Claude Sonnet 4.6 (Anthropic)",
    },
]

REPETITIONS = 3
