from pydantic import BaseModel, EmailStr
from typing import Optional, Literal


UserRole = Literal["general", "technical", "hr", "admin"]


class SignupRequest(BaseModel):
    """Fields accepted when a new employee account is created."""
    name: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = "general"


class LoginRequest(BaseModel):
    """Credentials accepted by the login endpoint."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Standard bearer-token response shape."""
    access_token: str
    token_type: str = "bearer"


class MessageItem(BaseModel):
    """One message in the conversation history sent to the RAG pipeline."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat input, including the session and recent conversation context."""
    session_id: str
    message: str
    history: list[MessageItem] = []


class ChatResponse(BaseModel):
    """Chat output with escalation and confidence information."""
    answer: str
    escalated: bool
    ticket_id: Optional[str] = None
    confidence: dict


class FeedbackRequest(BaseModel):
    """Feedback data stored against a chat session and optional ticket."""
    session_id: str
    user_query: str
    bot_answer: str
    rating: int
    comment: Optional[str] = None
    was_escalated: bool = False
    ticket_id: Optional[str] = None
