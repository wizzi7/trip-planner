import asyncio
from typing import Dict, Any, List
from backend.models import UserInput, TripDay

class WorldState:
    def __init__(self, user_input: UserInput):
        self.user_input = user_input
        self.constraints: Dict[str, Any] = {}
        self.days: List[TripDay] = []
        self.total_cost: float = 0.0

        self.lock = asyncio.Lock()

        self.constraints_ready = asyncio.Event()
        self.days_planned = asyncio.Event()
        self.cost_updated = asyncio.Event()
        self.plan_stable = asyncio.Event()
        
    async def update_constraints(self, constraints: Dict[str, Any]):
        async with self.lock:
            self.constraints = constraints
            self.constraints_ready.set()
            
    async def set_days(self, days: List[TripDay]):
        async with self.lock:
            self.days = days
            self.days_planned.set()
            
    async def update_day_content(self, day_index: int, field: str, data: Any):
        async with self.lock:
            if 0 <= day_index < len(self.days):
                setattr(self.days[day_index], field, data)
                
    async def add_cost(self, amount: float):
        async with self.lock:
            self.total_cost += amount
            self.cost_updated.set()
            self.cost_updated.clear()
            self.cost_updated.set()

    async def get_snapshot(self) -> Dict[str, Any]:
        async with self.lock:
            return {
                "constraints": self.constraints.copy(),
                "days": [d.model_copy() for d in self.days],
                "total_cost": self.total_cost
            }
