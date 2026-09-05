import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import tickets_col
from app.models import ChatRequest, ChatResponse
from app.rag import run_rag


router = APIRouter(prefix="/chat", tags=["Chat"])


def create_ticket(employee_id: str, email: str, session_id: str, query: str, history: list) -> str:
    """Persist an escalated conversation and return a human-readable ticket ID."""
    ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"

    ticket = {
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "employee_email": email,
        "session_id": session_id,
        "query": query,
        "conversation_history": [
            {"role": message.role, "content": message.content}
            for message in history
        ],
        "status": "open",
        "created_at": datetime.now(timezone.utc),
        "resolved_at": None,
        "agent_notes": None,
    }

    tickets_col.insert_one(ticket)
    return ticket_id


@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Run the RAG pipeline and create a ticket when confidence is insufficient."""
    history = [{"role": message.role, "content": message.content} for message in req.history]

    answer, should_escalate, confidence = run_rag(
        req.message,
        history,
        user_role=current_user["role"],
    )

    ticket_id = None
    if should_escalate:
        ticket_id = create_ticket(
            employee_id=str(current_user["user_id"]),
            email=current_user["email"],
            session_id=req.session_id,
            query=req.message,
            history=req.history,
        )
        answer = f"{answer}\n\nTicket ID: **{ticket_id}**"

    return ChatResponse(answer=answer, escalated=should_escalate, ticket_id=ticket_id, confidence=confidence)
