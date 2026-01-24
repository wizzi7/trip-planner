import asyncio
from backend.agents.orchestrator import OrchestratorAgent
from backend.models import UserInput

async def main():
    print("--- Starting Full Agent System Verification ---")

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
    
    print(f"\n[Main] Running Orchestrator for {user_input.destination}...")
    try:
        plan = await orchestrator.run(user_input)
        
        print("\n=== FINAL TRIP PLAN ===")
        print(f"Destination: {plan.destination}")
        print(f"Total Cost: {plan.total_cost:.2f} (Est)")
        if plan.metadata and "alerts" in plan.metadata:
            print("Alerts:")
            for alert in plan.metadata["alerts"]:
                print(f"  {alert}")
        
        print("\n--- Daily Itinerary ---")
        for day in plan.days:
            print(f"\nDay {day.day} ({day.date})")
            print(f"Theme: {day.theme}")
            print(f"Summary: {day.summary}")
            print(f"Cost: {day.estimated_cost}")
            print("Activities:")
            for act in day.activities:
                print(f"  - {act}")
                
    except Exception as e:
        print(f"\nFAILED to run orchestrator: {e}")

if __name__ == "__main__":
    asyncio.run(main())
