from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def storage_health():
    return {"service": "storage", "status": "coming in Phase 4"}
