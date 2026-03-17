from fastapi import APIRouter, Depends, HTTPException
from app.middleware.api_key import validate_api_key
from app.config import settings
from pydantic import BaseModel
from typing import Optional
import httpx

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: Optional[str] = "llama-3.3-70b-versatile"
    max_tokens: Optional[int] = 1024
    system: Optional[str] = None

async def call_groq(messages: list, model: str, max_tokens: int, system: str = None):
    formatted = []
    if system:
        formatted.append({"role": "system", "content": system})
    formatted += [{"role": m["role"], "content": m["content"]} for m in messages]

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": formatted,
                "max_tokens": max_tokens
            }
        )
        if response.status_code == 200:
            return response.json()
        return None

async def call_gemini(messages: list, max_tokens: int, system: str = None):
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": f"[System]: {system}"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})

    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}",
            json={
                "contents": contents,
                "generationConfig": {"maxOutputTokens": max_tokens}
            }
        )
        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"choices": [{"message": {"content": text}}]}
        return None

# ── Chat Endpoint ────────────────────────────────────────
@router.post("/chat")
async def chat(
    body: ChatRequest,
    project_id: str = Depends(validate_api_key)
):
    messages = [m.dict() for m in body.messages]

    # Try Groq first
    result = await call_groq(messages, body.model, body.max_tokens, body.system)

    # Fallback to Gemini if Groq fails
    if not result:
        result = await call_gemini(messages, body.max_tokens, body.system)

    if not result:
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")

    reply = result["choices"][0]["message"]["content"]

    return {
        "reply": reply,
        "model": body.model,
        "project_id": project_id
    }

# ── Health ───────────────────────────────────────────────
@router.get("/health")
def ai_health():
    return {"service": "ai", "status": "online", "models": ["llama-3.3-70b-versatile", "gemini-1.5-flash"]}
