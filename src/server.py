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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.tools.simple_rag_tool import SimpleRAG

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.agents.llm_wrapper import LLMWrapper
from src.agents.research_agent import ResearchAgent
from src.agents.analyse  import AnalysisAgent
from src.costs.cost_logger import CostLogger
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

from uuid import uuid4

# State
history = []
current_session_id = str(uuid4())
planner_agent = None
# documents : langchain_core.documents.Document
from langchain_core.documents import Document
document = Document(
    page_content="Hello, world!", metadata={"source": "https://example.com"}
)
rag = SimpleRAG.get_instance(LLMWrapper().model, documents=[document], embedding_model="mxbai-embed-large")
try:
    # Initialize Agents
    planner_agent = AnalysisAgent(rag=rag)
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

    def progress_callback(event_data):
        data = json.dumps({"type": "reflection_update", "content": event_data})
        q.put(f"data: {data}\n\n")

    def worker():
        try:
            response_content = planner_agent.handle_user_message(
                user_msg, 
                callback=progress_callback,
                session_id=current_session_id
            )
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
