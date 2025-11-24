from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import json
import queue
import threading
import time

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.agents.llm_wrapper import LLMWrapper
from src.agents.planner_agent import PlannerAgent
from src.agents.research_agent import ResearchAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.agents.fact_checker_agent import FactCheckerAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State
history = []
planner_agent = None

try:
    # Initialize Agents
    research_agent = ResearchAgent("Research")
    synthesis_agent = SynthesisAgent("Synthesis")
    fact_checker_agent = FactCheckerAgent("FactChecker")
    planner_agent = PlannerAgent("Planner", research_agent, synthesis_agent, fact_checker_agent)
    print("Agents initialized successfully.")
except Exception as e:
    print(f"Error initializing Agents: {e}")

SYSTEM_PROMPT = "You are a helpful assistant."

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not planner_agent:
        raise HTTPException(status_code=500, detail="Planner Agent not initialized")
    
    user_msg = request.message
    history.append({"role": "user", "content": user_msg})
    
    q = queue.Queue()

    def progress_callback(step, percentage):
        data = json.dumps({"type": "progress", "step": step, "percentage": percentage})
        q.put(f"data: {data}\n\n")

    def worker():
        try:
            response_content = planner_agent.handle_user_message(user_msg, progress_callback=progress_callback)
            history.append({"role": "assistant", "content": response_content})
            data = json.dumps({"type": "result", "content": response_content})
            q.put(f"data: {data}\n\n")
        except Exception as e:
            error_data = json.dumps({"type": "error", "content": str(e)})
            q.put(f"data: {error_data}\n\n")
        finally:
            q.put(None) # Signal end of stream

    threading.Thread(target=worker).start()

    def event_generator():
        while True:
            item = q.get()
            if item is None:
                break
            yield item

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/history")
async def get_history():
    return history

@app.delete("/history")
async def clear_history():
    global history
    history = []
    return {"status": "cleared"}

# Mount static files
# Ensure the directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
