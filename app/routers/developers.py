from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    DeveloperSignup, DeveloperLogin, TokenResponse,
    DeveloperResponse, ProjectCreate, ProjectResponse,
    APIKeyResponse, APIKeyInfo
)
from app.database import supabase
from app.utils.auth import hash_password, verify_password, create_jwt, get_current_developer
from app.utils.keys import generate_api_key, hash_key
import uuid

router = APIRouter()

# ── Signup ───────────────────────────────────────────────
@router.post("/signup", response_model=TokenResponse)
def signup(body: DeveloperSignup):
    # Check if email already exists
    existing = supabase.table("developers").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create developer
    dev_id = str(uuid.uuid4())
    new_dev = {
        "id": dev_id,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "full_name": body.full_name
    }
    result = supabase.table("developers").insert(new_dev).execute()
    dev = result.data[0]

    token = create_jwt(dev["id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "developer": {
            "id": dev["id"],
            "email": dev["email"],
            "full_name": dev["full_name"],
            "created_at": str(dev["created_at"])
        }
    }

# ── Login ────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(body: DeveloperLogin):
    result = supabase.table("developers").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    dev = result.data[0]
    if not verify_password(body.password, dev["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_jwt(dev["id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "developer": {
            "id": dev["id"],
            "email": dev["email"],
            "full_name": dev["full_name"],
            "created_at": str(dev["created_at"])
        }
    }

# ── Get current developer profile ───────────────────────
@router.get("/me", response_model=DeveloperResponse)
def get_me(dev_id: str = Depends(get_current_developer)):
    result = supabase.table("developers").select("*").eq("id", dev_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Developer not found")
    dev = result.data[0]
    return {
        "id": dev["id"],
        "email": dev["email"],
        "full_name": dev["full_name"],
        "created_at": str(dev["created_at"])
    }

# ── Create Project ───────────────────────────────────────
@router.post("/projects", response_model=ProjectResponse)
def create_project(body: ProjectCreate, dev_id: str = Depends(get_current_developer)):
    project_id = str(uuid.uuid4())
    result = supabase.table("projects").insert({
        "id": project_id,
        "developer_id": dev_id,
        "name": body.name,
        "description": body.description
    }).execute()
    proj = result.data[0]
    return {
        "id": proj["id"],
        "name": proj["name"],
        "description": proj["description"],
        "created_at": str(proj["created_at"])
    }

# ── List Projects ────────────────────────────────────────
@router.get("/projects")
def list_projects(dev_id: str = Depends(get_current_developer)):
    result = supabase.table("projects").select("*").eq("developer_id", dev_id).execute()
    return result.data

# ── Generate API Key ─────────────────────────────────────
@router.post("/projects/{project_id}/keys", response_model=APIKeyResponse)
def create_api_key(project_id: str, dev_id: str = Depends(get_current_developer)):
    # Verify project belongs to this developer
    proj = supabase.table("projects").select("*").eq("id", project_id).eq("developer_id", dev_id).execute()
    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate key
    raw_key, prefix, key_hash = generate_api_key()
    key_id = str(uuid.uuid4())

    result = supabase.table("api_keys").insert({
        "id": key_id,
        "project_id": project_id,
        "key_hash": key_hash,
        "key_prefix": prefix
    }).execute()
    key = result.data[0]

    return {
        "id": key["id"],
        "key": raw_key,       # shown ONCE — never stored in plain text
        "key_prefix": prefix,
        "project_id": project_id,
        "created_at": str(key["created_at"])
    }

# ── List API Keys for a project ──────────────────────────
@router.get("/projects/{project_id}/keys")
def list_api_keys(project_id: str, dev_id: str = Depends(get_current_developer)):
    proj = supabase.table("projects").select("*").eq("id", project_id).eq("developer_id", dev_id).execute()
    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    result = supabase.table("api_keys").select("id, key_prefix, project_id, created_at, last_used_at, is_active").eq("project_id", project_id).execute()
    return result.data

# ── Revoke API Key ───────────────────────────────────────
@router.delete("/projects/{project_id}/keys/{key_id}")
def revoke_api_key(project_id: str, key_id: str, dev_id: str = Depends(get_current_developer)):
    proj = supabase.table("projects").select("*").eq("id", project_id).eq("developer_id", dev_id).execute()
    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    supabase.table("api_keys").update({"is_active": False}).eq("id", key_id).execute()
    return {"message": "API key revoked successfully"}
