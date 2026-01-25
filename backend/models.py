from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LLMSettings(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000

class UserInput(BaseModel):
    destination: str
    arrival: str
    departure: str
    guests: int
    budget: float
    pace: str
    transport: List[str]
    accommodation: Optional[str] = None
    extra_req: Optional[str] = None
    llm_settings: Optional[LLMSettings] = None

class TripDay(BaseModel):
    day: int
    date: str
    theme: str
    summary: str
    activities: List[str]
    estimated_cost: str
    meals: Dict[str, str] = {}

class TripPlan(BaseModel):
    destination: str
    total_cost: float
    days: List[TripDay]
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata from agents (e.g. constraints)")

class UpdateRequest(BaseModel):
    current_plan: TripPlan
    feedback: str
    user_input: UserInput
