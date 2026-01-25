import pytest
from backend.agents.orchestrator import OrchestratorAgent
from backend.models import UserInput

@pytest.mark.asyncio
async def test_gastronomy_and_activity_limits():
    print("\n--- Starting Gastronomy and Activity Limit Test ---")

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
    assert len(plan.days) > 0, "Plan should have days"
    
    for day in plan.days:
        print(f"\nDay {day.day} Summary:")
        print(f"Activities Count: {len(day.activities)}")
        print(f"Activities: {day.activities}")

        if len(day.activities) < 6:
             pytest.fail(f"Day {day.day} has {len(day.activities)} activities (Target: >= 6)")
        
        print(f"Meals: {day.meals}")
        expected_meals = ["breakfast", "lunch", "dinner", "snack"]
        missing_meals = [k for k in expected_meals if k not in day.meals]
        
        if missing_meals:
            pytest.fail(f"Day {day.day} missing meal types: {missing_meals}")
            
    print("\nSUCCESS: All days have required activities and meals.")
