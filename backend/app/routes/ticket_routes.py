from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import tickets_col


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/")
def get_all_tickets(
    status: str = None,
    current_user: dict = Depends(get_current_user),
):
    """Return the newest tickets, optionally filtered by status, with totals."""
    query = {}
    if status:
        query["status"] = status

    tickets = list(
        tickets_col.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(100)
    )
    return {
        "tickets": tickets,
        "total": len(tickets),
        "open": tickets_col.count_documents({"status": "open"}),
        "resolved": tickets_col.count_documents({"status": "resolved"}),
    }


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    """Return one ticket without exposing MongoDB's internal identifier."""
    ticket = tickets_col.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a ticket resolved and record who resolved it and when."""
    result = tickets_col.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status": "resolved",
            "resolved_at": datetime.now(timezone.utc),
            "resolved_by": current_user["email"],
        }},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": f"Ticket {ticket_id} marked as resolved"}


@router.get("/stats/overview")
def ticket_stats(current_user: dict = Depends(get_current_user)):
    """Return aggregate ticket counts for the dashboard."""
    return {
        "total": tickets_col.count_documents({}),
        "open": tickets_col.count_documents({"status": "open"}),
        "resolved": tickets_col.count_documents({"status": "resolved"}),
    }
