from cgitb import reset

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
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.agents.llm_wrapper import LLMWrapper
from src.agents.research_agent import ResearchAgent
from src.agents.analyse_agent  import AnalysisAgent
from src.agents.formatting_agent import FormattingAgent
from src.costs.cost_logger import CostLogger
from src.tools.agent_tools import max_articles_context
from dotenv import load_dotenv
import contextvars

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

from uuid import uuid4

# State
history = []
current_session_id = str(uuid4())
planner_agent = None
formatting_agent = None
active_sessions = {} # Map session_id -> stop_event

# documents : langchain_core.documents.Document
from langchain_core.documents import Document
try:
    # Initialize Agents
    planner_agent = AnalysisAgent()
    formatting_agent = FormattingAgent()
    print("Agents initialized successfully.")
except Exception as e:
    print(f"Error initializing Agents: {e}")

SYSTEM_PROMPT = "You are a helpful assistant."

class ChatRequest(BaseModel):
    message: str
    max_iterations: Optional[int] = 15
    max_articles: Optional[int] = 5

class StopRequest(BaseModel):
    session_id: Optional[str] = None

@app.post("/stop")
async def stop_endpoint(request: StopRequest):
    # If session_id provided, stop that specific session
    # Otherwise stop the current global session
    target_session = request.session_id or current_session_id
    
    if target_session in active_sessions:
        active_sessions[target_session].set()
        return {"status": "stopped", "session_id": target_session}
    
    return {"status": "not_found", "session_id": target_session}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not planner_agent:
        raise HTTPException(status_code=500, detail="Planner Agent not initialized")
    user_msg = request.message
    history.append({"role": "user", "content": user_msg})
    q = queue.Queue()

    # Create stop event for this request
    stop_event = threading.Event()
    active_sessions[current_session_id] = stop_event
    
    # Set context var for this request
    token = max_articles_context.set(request.max_articles)
    
    # Capture context to run in thread
    ctx = contextvars.copy_context()

    def progress_callback(event_data):
        # Handle direct status updates
        if event_data.get("type") == "status":
            data = json.dumps(event_data)
            q.put(f"data: {data}\n\n")
            return

        # Handle tool-based status updates
        if event_data.get("type") == "tool_start":
            tool_name = event_data.get("tool", "")
            if "research" in tool_name.lower():
                q.put(f"data: {json.dumps({'type': 'status', 'status': 'Researching...'})}\n\n")
            elif "synthesis" in tool_name.lower():
                q.put(f"data: {json.dumps({'type': 'status', 'status': 'Synthesizing...'})}\n\n")

        data = json.dumps({"type": "reflection_update", "content": event_data})
        q.put(f"data: {data}\n\n")

    def worker():
        try:
            # Initial status
            q.put(f"data: {json.dumps({'type': 'status', 'status': 'Analyzing...'})}\n\n")
            
            response_data = planner_agent.handle_user_message(
                user_msg, 
                callback=progress_callback,
                session_id=current_session_id,
                max_iterations=request.max_iterations,
                stop_event=stop_event
            )
            
            # Handle both string (legacy) and dict (new) responses
            if isinstance(response_data, dict):
                raw_content = response_data.get("content", "")
                available_sources = response_data.get("sources", [])
                
                # Call Formatting Agent here
                q.put(f"data: {json.dumps({'type': 'status', 'status': 'Formatting response...'})}\n\n")
                formatted_content, used_sources = formatting_agent.format_response(raw_content, available_sources)
                
                history.append({"role": "assistant", "content": formatted_content})
                data = json.dumps({
                    "type": "result", 
                    "content": formatted_content,
                    "sources": used_sources
                })
                q.put(f"data: {data}\n\n")
            else:
                # Legacy string response
                history.append({"role": "assistant", "content": response_data})
                data = json.dumps({"type": "result", "content": response_data})
                q.put(f"data: {data}\n\n")
                
        except Exception as e:
            print(f"Error in worker: {e}")
            data = json.dumps({"type": "error", "content": str(e)})
            q.put(f"data: {data}\n\n")
        finally:
            q.put(None)  # Signal end
            if current_session_id in active_sessions:
                del active_sessions[current_session_id]
            
            # Reset context var (though in thread it doesn't matter much, but good practice if reused)
            # Actually we can't reset in the thread for the parent, but we can reset in parent finally block if we waited.
            # Since we don't wait, we rely on contextvars being thread-local or copied.

    def worker_wrapper():
        ctx.run(worker)

    t = threading.Thread(target=worker_wrapper)
    t.start()

    def stream():
        while True:
            msg = q.get()
            if msg is None:
                break
            yield msg

    return StreamingResponse(stream(), media_type="text/event-stream")

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

    def progress_callback(event_data):
        data = json.dumps({"type": "reflection_update", "content": event_data})
        q.put(f"data: {data}\n\n")

    def worker():
        try:
            response_data = planner_agent.handle_user_message(
                user_msg, 
                callback=progress_callback,
                session_id=current_session_id
            )
            
            # Handle both string (legacy) and dict (new) responses
            if isinstance(response_data, dict):
                raw_content = response_data.get("content", "")
                available_sources = response_data.get("sources", [])
                
                # Call Formatting Agent here
                formatted_content, used_sources = formatting_agent.format_response(raw_content, available_sources)
                
                history.append({"role": "assistant", "content": formatted_content})
                data = json.dumps({
                    "type": "result", 
                    "content": formatted_content,
                    "sources": used_sources
                })
            else:
                history.append({"role": "assistant", "content": response_data})
                data = json.dumps({"type": "result", "content": response_data})
                
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

@app.get("/costs")
async def get_costs():
    logger = CostLogger()
    return logger.get_stats(session_id=current_session_id)

@app.delete("/history")
async def clear_history():
    global history, current_session_id
    history = []
    current_session_id = str(uuid4())
    return {"status": "cleared"}
    return {"status": "cleared"}

# Mount static files
# Ensure the directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
