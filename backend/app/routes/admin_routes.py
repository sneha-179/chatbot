from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_role
from app.database import users_col


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(current_user: dict = Depends(require_role("admin"))):
    """List users while excluding password hashes from the response."""
    users = list(users_col.find({}, {"password_hash": 0}))
    for user in users:
        user["_id"] = str(user["_id"])
    return {"users": users}


@router.patch("/users/{user_id}/role")
def change_role(
    user_id: str,
    new_role: str,
    current_user: dict = Depends(require_role("admin")),
):
    """Change an account role after validating the requested role name."""
    if new_role not in ("general", "technical", "hr", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    result = users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": new_role}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User role updated to {new_role}"}
