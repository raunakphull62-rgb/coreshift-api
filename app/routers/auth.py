from fastapi import APIRouter, Depends, HTTPException, Header
from app.middleware.api_key import validate_api_key
from app.database import supabase
from app.utils.auth import hash_password, verify_password
from pydantic import BaseModel
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uuid
import os

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "coreshift_secret")

class UserSignup(BaseModel):
    email: str
    password: str
    metadata: Optional[dict] = {}

class UserLogin(BaseModel):
    email: str
    password: str

def create_user_jwt(user_id: str, project_id: str) -> str:
    payload = {
        "sub": user_id,
        "project_id": project_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ── User Signup ──────────────────────────────────────────
@router.post("/signup")
def user_signup(
    body: UserSignup,
    project_id: str = Depends(validate_api_key)
):
    existing = supabase.table("project_users")\
        .select("id")\
        .eq("project_id", project_id)\
        .eq("email", body.email)\
        .execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    result = supabase.table("project_users").insert({
        "id": user_id,
        "project_id": project_id,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "metadata": body.metadata
    }).execute()

    user = result.data[0]
    token = create_user_jwt(user_id, project_id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "metadata": user["metadata"],
            "created_at": str(user["created_at"])
        }
    }

# ── User Login ───────────────────────────────────────────
@router.post("/login")
def user_login(
    body: UserLogin,
    project_id: str = Depends(validate_api_key)
):
    result = supabase.table("project_users")\
        .select("*")\
        .eq("project_id", project_id)\
        .eq("email", body.email)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = result.data[0]
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_user_jwt(user["id"], project_id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "metadata": user["metadata"],
            "created_at": str(user["created_at"])
        }
    }

# ── Get Current User ─────────────────────────────────────
@router.get("/me")
def get_user(
    project_id: str = Depends(validate_api_key),
    token_data: dict = Depends(get_current_user)
):
    result = supabase.table("project_users")\
        .select("id, email, metadata, created_at")\
        .eq("id", token_data["sub"])\
        .eq("project_id", project_id)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data[0]

# ── List Users (admin) ───────────────────────────────────
@router.get("/users")
def list_users(project_id: str = Depends(validate_api_key)):
    result = supabase.table("project_users")\
        .select("id, email, metadata, created_at")\
        .eq("project_id", project_id)\
        .execute()
    return {"count": len(result.data), "users": result.data}

# ── Delete User ──────────────────────────────────────────
@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    project_id: str = Depends(validate_api_key)
):
    supabase.table("project_users")\
        .delete()\
        .eq("id", user_id)\
        .eq("project_id", project_id)\
        .execute()
    return {"message": "User deleted successfully"}
