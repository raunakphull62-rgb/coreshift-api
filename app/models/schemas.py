from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ── Developer Auth ──────────────────────────────────────
class DeveloperSignup(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class DeveloperLogin(BaseModel):
    email: str
    password: str

class DeveloperResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    developer: DeveloperResponse

# ── Projects ─────────────────────────────────────────────
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str

# ── API Keys ─────────────────────────────────────────────
class APIKeyResponse(BaseModel):
    id: str
    key: str          # shown ONCE at creation only
    key_prefix: str
    project_id: str
    created_at: str

class APIKeyInfo(BaseModel):
    id: str
    key_prefix: str
    project_id: str
    created_at: str
    last_used_at: Optional[str]
    is_active: bool
