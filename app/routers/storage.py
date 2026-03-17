from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from app.middleware.api_key import validate_api_key
from app.database import supabase
import uuid
import httpx

router = APIRouter()

BUCKET_NAME = "coreshift-storage"

# ── Upload File ──────────────────────────────────────────
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Depends(validate_api_key)
):
    # Validate file size (max 10MB per file)
    contents = await file.read()
    size = len(contents)

    if size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB")

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_name = f"{project_id}/{uuid.uuid4()}.{ext}"

    # Upload to Supabase Storage
    result = supabase.storage.from_(BUCKET_NAME).upload(
        path=unique_name,
        file=contents,
        file_options={"content-type": file.content_type or "application/octet-stream"}
    )

    # Get public URL
    url_result = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)

    # Save file metadata to DB
    file_id = str(uuid.uuid4())
    supabase.table("project_files").insert({
        "id": file_id,
        "project_id": project_id,
        "filename": file.filename,
        "storage_url": url_result,
        "size_bytes": size
    }).execute()

    return {
        "id": file_id,
        "filename": file.filename,
        "url": url_result,
        "size_bytes": size,
        "message": "File uploaded successfully"
    }

# ── List Files ───────────────────────────────────────────
@router.get("/files")
def list_files(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    project_id: str = Depends(validate_api_key)
):
    result = supabase.table("project_files")\
        .select("id, filename, storage_url, size_bytes, created_at")\
        .eq("project_id", project_id)\
        .range(offset, offset + limit - 1)\
        .execute()

    return {
        "count": len(result.data),
        "files": result.data
    }

# ── Get Single File Info ─────────────────────────────────
@router.get("/files/{file_id}")
def get_file(
    file_id: str,
    project_id: str = Depends(validate_api_key)
):
    result = supabase.table("project_files")\
        .select("*")\
        .eq("id", file_id)\
        .eq("project_id", project_id)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="File not found")

    return result.data[0]

# ── Delete File ──────────────────────────────────────────
@router.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    project_id: str = Depends(validate_api_key)
):
    # Get file info first
    result = supabase.table("project_files")\
        .select("*")\
        .eq("id", file_id)\
        .eq("project_id", project_id)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="File not found")

    file = result.data[0]

    # Extract storage path from URL
    storage_path = f"{project_id}/{file['filename']}"

    # Delete from Supabase Storage
    try:
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
    except:
        pass  # Continue even if storage delete fails

    # Delete from DB
    supabase.table("project_files")\
        .delete()\
        .eq("id", file_id)\
        .execute()

    return {"message": "File deleted successfully"}

# ── Health ───────────────────────────────────────────────
@router.get("/health")
def storage_health():
    return {"service": "storage", "status": "online", "provider": "Supabase Storage"}
