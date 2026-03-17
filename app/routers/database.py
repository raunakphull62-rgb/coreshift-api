from fastapi import APIRouter, Depends, HTTPException, Query
from app.middleware.api_key import validate_api_key
from app.database import supabase
from pydantic import BaseModel
from typing import Optional, Any
import uuid

router = APIRouter()

class DocumentCreate(BaseModel):
    data: dict

class DocumentUpdate(BaseModel):
    data: dict

# ── Create Collection ────────────────────────────────────
@router.post("/collections/{collection_name}")
def create_collection(
    collection_name: str,
    project_id: str = Depends(validate_api_key)
):
    existing = supabase.table("project_collections")\
        .select("id")\
        .eq("project_id", project_id)\
        .eq("name", collection_name)\
        .execute()

    if existing.data:
        return {"message": f"Collection '{collection_name}' already exists"}

    supabase.table("project_collections").insert({
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "name": collection_name
    }).execute()

    return {"message": f"Collection '{collection_name}' created successfully"}

# ── List Collections ─────────────────────────────────────
@router.get("/collections")
def list_collections(project_id: str = Depends(validate_api_key)):
    result = supabase.table("project_collections")\
        .select("*")\
        .eq("project_id", project_id)\
        .execute()
    return result.data

# ── Insert Document ──────────────────────────────────────
@router.post("/{collection_name}")
def insert_document(
    collection_name: str,
    body: DocumentCreate,
    project_id: str = Depends(validate_api_key)
):
    doc_id = str(uuid.uuid4())
    result = supabase.table("project_documents").insert({
        "id": doc_id,
        "project_id": project_id,
        "collection_name": collection_name,
        "data": body.data
    }).execute()
    return {"id": doc_id, "data": body.data, "message": "Document created"}

# ── Get All Documents in Collection ─────────────────────
@router.get("/{collection_name}")
def get_documents(
    collection_name: str,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    project_id: str = Depends(validate_api_key)
):
    result = supabase.table("project_documents")\
        .select("*")\
        .eq("project_id", project_id)\
        .eq("collection_name", collection_name)\
        .range(offset, offset + limit - 1)\
        .execute()
    return {
        "collection": collection_name,
        "count": len(result.data),
        "documents": result.data
    }

# ── Get Single Document ──────────────────────────────────
@router.get("/{collection_name}/{doc_id}")
def get_document(
    collection_name: str,
    doc_id: str,
    project_id: str = Depends(validate_api_key)
):
    result = supabase.table("project_documents")\
        .select("*")\
        .eq("project_id", project_id)\
        .eq("collection_name", collection_name)\
        .eq("id", doc_id)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    return result.data[0]

# ── Update Document ──────────────────────────────────────
@router.patch("/{collection_name}/{doc_id}")
def update_document(
    collection_name: str,
    doc_id: str,
    body: DocumentUpdate,
    project_id: str = Depends(validate_api_key)
):
    existing = supabase.table("project_documents")\
        .select("id, data")\
        .eq("project_id", project_id)\
        .eq("collection_name", collection_name)\
        .eq("id", doc_id)\
        .execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Document not found")

    # Merge existing data with new data
    merged = {**existing.data[0]["data"], **body.data}

    supabase.table("project_documents")\
        .update({"data": merged})\
        .eq("id", doc_id)\
        .execute()

    return {"id": doc_id, "data": merged, "message": "Document updated"}

# ── Delete Document ──────────────────────────────────────
@router.delete("/{collection_name}/{doc_id}")
def delete_document(
    collection_name: str,
    doc_id: str,
    project_id: str = Depends(validate_api_key)
):
    existing = supabase.table("project_documents")\
        .select("id")\
        .eq("project_id", project_id)\
        .eq("collection_name", collection_name)\
        .eq("id", doc_id)\
        .execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Document not found")

    supabase.table("project_documents")\
        .delete()\
        .eq("id", doc_id)\
        .execute()

    return {"message": "Document deleted successfully"}
