from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.auth import create_access_token, hash_password, verify_password
from app.database import users_col
from app.models import LoginRequest, SignupRequest


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", status_code=201)
def signup(req: SignupRequest):
    """Create a general, technical, or HR account and return its access token."""
    if users_col.find_one({"email": req.email}):
        raise HTTPException(status_code=409, detail="Email already registered")

    safe_role = req.role if req.role in ("general", "technical", "hr") else "general"

    user = {
        "name": req.name,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "role": safe_role,
        "created_at": datetime.now(timezone.utc),
    }
    result = users_col.insert_one(user)
    user_id = str(result.inserted_id)

    token = create_access_token(user_id, req.email, safe_role)
    return {"message": "Account created", "access_token": token, "role": safe_role}


@router.post("/login")
def login(req: LoginRequest):
    """Authenticate an existing account without revealing which field failed."""
    user = users_col.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    role = user.get("role", "general")
    token = create_access_token(str(user["_id"]), user["email"], role)
    return {"message": "Login successful", "access_token": token, "role": role}
