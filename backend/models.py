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
    interests: List[str] = Field(default_factory=list)
    extra_req: Optional[str] = None
    llm_settings: Optional[LLMSettings] = None

class TripDay(BaseModel):
    day: int
    date: str
    theme: str
    summary: str
    activities: List[str]
    estimated_cost: str

class CulinaryDish(BaseModel):
    name: str = "Unknown Dish"
    description: str = "No description available."
    price_range: str = "N/A"

class CulinaryVenue(BaseModel):
    name: str = "Unknown Venue"
    price_range: str = "N/A"
    type: Optional[str] = "Local"
    signature_items: Optional[str] = "Various options"
    district: str = "City Center"

class CulinarySection(BaseModel):
    main_dishes: List[CulinaryDish] = Field(default_factory=list)
    soups: List[CulinaryDish] = Field(default_factory=list)
    desserts: List[CulinaryDish] = Field(default_factory=list)
    drinks: List[CulinaryDish] = Field(default_factory=list)
    venues_traditional: List[CulinaryVenue] = Field(default_factory=list)
    venues_cafes: List[CulinaryVenue] = Field(default_factory=list)
    venues_bars: List[CulinaryVenue] = Field(default_factory=list)

class UsageStats(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    model: str

class TripPlan(BaseModel):
    destination: str
    total_cost: float
    days: List[TripDay]
    usage_stats: Dict[str, UsageStats] = Field(default_factory=dict)
    culinary_section: Optional[CulinarySection] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata from agents (e.g. constraints)")

class UpdateRequest(BaseModel):
    current_plan: TripPlan
    feedback: str
    user_input: UserInput
