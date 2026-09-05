from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import feedback_col
from app.models import FeedbackRequest


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/", status_code=201)
def submit_feedback(req: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Store feedback together with the authenticated employee identity."""
    feedback_doc = {
        "session_id": req.session_id,
        "employee_id": current_user["user_id"],
        "employee_email": current_user["email"],
        "user_query": req.user_query,
        "bot_answer": req.bot_answer,
        "rating": req.rating,
        "comment": req.comment,
        "was_escalated": req.was_escalated,
        "ticket_id": req.ticket_id,
        "submitted_at": datetime.now(timezone.utc),
    }
    feedback_col.insert_one(feedback_doc)
    return {"message": "Feedback recorded. Thank you!"}


@router.get("/summary")
def feedback_summary(current_user: dict = Depends(get_current_user)):
    """Return dashboard metrics and the most recent negative feedback."""
    total = feedback_col.count_documents({})
    positive = feedback_col.count_documents({"rating": 1})
    negative = feedback_col.count_documents({"rating": -1})

    negative_entries = list(
        feedback_col.find({"rating": -1}, {"_id": 0})
        .sort("submitted_at", -1)
        .limit(50)
    )

    escalated_positive = feedback_col.count_documents({
        "was_escalated": True,
        "rating": 1,
    })

    answered_negative = feedback_col.count_documents({
        "was_escalated": False,
        "rating": -1,
    })

    return {
        "total_feedback": total,
        "positive": positive,
        "negative": negative,
        "escalated_positive": escalated_positive,
        "answered_negative": answered_negative,
        "negative_entries": negative_entries,
    }


@router.get("/all")
def get_all_feedback(current_user: dict = Depends(get_current_user)):
    """Return the most recent feedback records for an authorized user."""
    entries = list(
        feedback_col.find({}, {"_id": 0})
        .sort("submitted_at", -1)
        .limit(100)
    )
    return {"feedback": entries, "total": len(entries)}
