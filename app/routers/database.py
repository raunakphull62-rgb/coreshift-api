from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def db_health():
    return {"service": "database", "status": "coming soon"}
