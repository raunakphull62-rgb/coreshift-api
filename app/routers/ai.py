from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def ai_health():
    return {"service": "ai", "status": "coming soon"}
