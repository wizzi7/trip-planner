import pytest
from backend.agents.orchestrator import OrchestratorAgent
from backend.models import UserInput

@pytest.mark.asyncio
async def test_full_workflow():
    print("\n--- Starting End-to-End Workflow Test ---")

    user_input = UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["Taxi/Uber"],
        accommodation="hotel",
        extra_req="I want to see historic sites and eat pierogi."
    )
    
    orchestrator = OrchestratorAgent()
    
    print(f"\n[Test] Running Orchestrator for {user_input.destination}...")
    
    plan = await orchestrator.run(user_input)

    assert plan is not None, "Plan should not be None"
    assert plan.destination == "Warsaw, Poland", "Destination should match input"
    assert len(plan.days) == 3, "Should be a 3-day trip"
    assert plan.total_cost > 0, "Total cost should be calculated"

    themes = [day.theme.lower() for day in plan.days]
    print(f"Generated Themes: {themes}")
    assert len(themes) > 0, "Should have themes"
    
    print("\n=== FINAL TRIP PLAN VERIFIED ===")
    print(f"Total Cost: {plan.total_cost}")
