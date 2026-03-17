from fastapi import Header, HTTPException, Depends
from app.database import supabase
from app.utils.keys import hash_key
from datetime import datetime

def validate_api_key(x_coreshift_key: str = Header(..., alias="X-CoreShift-Key")):
    """
    Every protected endpoint calls this.
    Validates the API key and returns the project_id.
    """
    if not x_coreshift_key.startswith("cs_live_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    key_hash = hash_key(x_coreshift_key)

    result = supabase.table("api_keys")\
        .select("id, project_id, is_active")\
        .eq("key_hash", key_hash)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid API key")

    key = result.data[0]

    if not key["is_active"]:
        raise HTTPException(status_code=401, detail="API key has been revoked")

    # Update last_used_at
    supabase.table("api_keys")\
        .update({"last_used_at": datetime.utcnow().isoformat()})\
        .eq("id", key["id"])\
        .execute()

    return key["project_id"]
