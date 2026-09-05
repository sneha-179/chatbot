from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bm25_index import build_bm25_index
from app.ingestion import run_startup_indexing
from app.routes.admin_routes import router as admin_router
from app.routes.auth_routes import router as auth_router
from app.routes.chat_routes import router as chat_router
from app.routes.feedback_routes import router as feedback_router
from app.routes.ingest_routes import router as ingest_router
from app.routes.ticket_routes import router as ticket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Refresh retrieval indexes before the API starts accepting requests."""
    print("[Startup] Indexing knowledge base...")
    run_startup_indexing()
    build_bm25_index()
    print("[Startup] Ready!")
    yield


app = FastAPI(title="RAG Helpdesk Chatbot API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(feedback_router)
app.include_router(ingest_router)
app.include_router(ticket_router)
app.include_router(admin_router)


@app.get("/")
def health():
    """Provide a lightweight health response for local checks and monitoring."""
    return {"status": "ok", "version": "2.0.0"}
