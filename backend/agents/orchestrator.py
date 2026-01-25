from backend.models import UserInput, TripPlan
from backend.agents.base import BaseAgent
from backend.agents.preferences import PreferencesAgent
from backend.agents.attractions import AttractionsAgent
from backend.agents.transport import TransportationAgent
from backend.agents.budget import BudgetAgent
from backend.agents.gastronomy import GastronomyAgent

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Orchestrator")
        self.preferences_agent = PreferencesAgent()
        self.attractions_agent = AttractionsAgent()
        self.gastronomy_agent = GastronomyAgent()
        self.transport_agent = TransportationAgent()
        self.budget_agent = BudgetAgent()

    async def run(self, user_input: UserInput) -> TripPlan:
        print(f"[{self.name}] Starting planning for {user_input.destination}")
        
        # 1. Preferences Agent
        constraints = await self.preferences_agent.run(user_input)
        
        # 2. Attractions Agent
        days = await self.attractions_agent.run(user_input, constraints)
        
        # 3. Gastronomy Agent
        days = await self.gastronomy_agent.run(user_input, days)

        # 4. Transportation Agent
        days = await self.transport_agent.run(user_input, days)

        plan = TripPlan(
            destination=user_input.destination,
            total_cost=0,
            days=days,
            metadata={"constraints": constraints}
        )
        
        # 5. Budget Agent
        plan = await self.budget_agent.run(user_input, plan)
        
        print(f"[{self.name}] Plan generated successfully.")
        return plan
