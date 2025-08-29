from fastapi import FastAPI
from pydantic import BaseModel
from src.main import chat_once
import traceback

app = FastAPI()

class ChatRequest(BaseModel):
    question: str
    role: str = "employee"
    user_id: str = "default"

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        route, ans = chat_once(req.question, role=req.role, user_id=req.user_id)
        return {"route": route, "answer": ans}
    except Exception as e:
        tb = traceback.format_exc()
        return {"error": str(e), "traceback": tb}
