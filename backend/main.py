from fastapi import FastAPI, HTTPException
from backend.models import UserInput, TripPlan, UpdateRequest, LLMSettings
from backend.agents.orchestrator import OrchestratorAgent
from backend.agents.feedback import FeedbackAgent
from backend.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent Trip Planner API")
feedback_agent = FeedbackAgent()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/generate_plan", response_model=TripPlan)
async def generate_plan(user_input: UserInput):
    try:
        if not user_input.llm_settings:
             user_input.llm_settings = LLMSettings()

        logger.info(f"Received request for {user_input.destination}")
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(user_input)
        return plan

    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_plan", response_model=TripPlan)
async def update_plan(request: UpdateRequest):
    try:
        updated_input, directives = await feedback_agent.run(request.current_plan, request.user_input, request.feedback)
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(updated_input)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
