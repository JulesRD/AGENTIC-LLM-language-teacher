from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.agents.llm_wrapper import LLMWrapper
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
try:
    llm = LLMWrapper()
except Exception as e:
    print(f"Error initializing LLMWrapper: {e}")
    llm = None

SYSTEM_PROMPT = "You are a helpful assistant."

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not initialized")
    
    user_msg = request.message
    history.append({"role": "user", "content": user_msg})
    
    try:
        # Using the requested LLMWrapper.chat method
        response_content = llm.chat(SYSTEM_PROMPT, user_msg)
        history.append({"role": "assistant", "content": response_content})
        return {"response": response_content, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
