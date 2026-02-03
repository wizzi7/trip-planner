from fastapi import FastAPI, HTTPException
from backend.models import UserInput, TripPlan, UpdateRequest
from backend.agents.orchestrator import OrchestratorAgent
from backend.agents.feedback import FeedbackAgent
from backend.logging_config import setup_logging

setup_logging()

app = FastAPI(title="Intelligent Trip Planner API")
orchestrator = OrchestratorAgent()
feedback_agent = FeedbackAgent()

@app.post("/generate_plan", response_model=TripPlan)
async def generate_plan(user_input: UserInput):
    try:
        plan = await orchestrator.run(user_input)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_plan", response_model=TripPlan)
async def update_plan(request: UpdateRequest):
    try:
        updated_input, directives = await feedback_agent.run(request.current_plan, request.user_input, request.feedback)
        plan = await orchestrator.run(updated_input)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
