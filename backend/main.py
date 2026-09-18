"""
main.py
-------
The FastAPI backend application for the Student Support Assistant.

Run this with (from the project root, virtual environment activated):

    uvicorn backend.main:app --reload

Endpoints:
    GET  /        -> health check
    POST /chat    -> ask a question
    POST /reset   -> clear a session's conversation memory
    POST /ingest  -> re-run document ingestion without leaving the server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import is_api_key_configured
from backend.memory import memory_store
from backend.chat.assistant import get_answer
from backend.rag.ingest import run_ingestion
from backend.rag.retriever import is_knowledge_base_ready

app = FastAPI(title="Student Support Assistant API")

# Allow the frontend (served from a different origin/port, e.g. opening
# index.html directly or via Live Server) to talk to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# Request/response models (these give us automatic validation + docs)
# ---------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list
    session_id: str


class ResetRequest(BaseModel):
    session_id: str


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@app.get("/")
def health_check():
    """Basic status endpoint. Also reports whether the API key and
    knowledge base are ready, which is handy for debugging."""
    return {
        "status": "ok",
        "message": "Student Support Assistant backend is running.",
        "api_key_configured": is_api_key_configured(),
        "knowledge_base_ready": is_knowledge_base_ready(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # --- Validate the API key is present before doing anything else ---
    if not is_api_key_configured():
        return ChatResponse(
            answer=(
                "The Gemini API key is missing. Please create a .env file "
                "in the project root with GEMINI_API_KEY=your_api_key_here "
                "and restart the backend server."
            ),
            sources=[],
            session_id=request.session_id,
        )

    # --- Validate session id ------------------------------------------
    session_id = (request.session_id or "").strip()
    if not session_id:
        return ChatResponse(
            answer="A valid session_id is required. Please refresh the page and try again.",
            sources=[],
            session_id=session_id,
        )

    # --- Validate the message is not empty -----------------------------
    message = (request.message or "").strip()
    if not message:
        return ChatResponse(
            answer="Please type a question before sending.",
            sources=[],
            session_id=session_id,
        )

    # --- Call the assistant, catching any errors gracefully -------------
    try:
        result = get_answer(session_id, message)
    except RuntimeError as e:
        # Errors we raised ourselves in assistant.py (API key issues,
        # Gemini API errors) already have friendly messages.
        return ChatResponse(answer=str(e), sources=[], session_id=session_id)
    except Exception as e:
        return ChatResponse(
            answer=f"Something went wrong while processing your question: {e}",
            sources=[],
            session_id=session_id,
        )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=session_id,
    )


@app.post("/reset")
def reset(request: ResetRequest):
    session_id = (request.session_id or "").strip()
    if not session_id:
        return {"status": "error", "message": "A valid session_id is required."}

    cleared = memory_store.reset_session(session_id)
    return {
        "status": "ok",
        "cleared": cleared,
        "message": "Conversation memory cleared." if cleared else "No memory found for this session (nothing to clear).",
    }


@app.post("/ingest")
def ingest():
    """Re-runs document ingestion from within the running server. Useful
    if you add new documents and don't want to restart anything manually."""
    try:
        run_ingestion()
    except Exception as e:
        return {"status": "error", "message": f"Ingestion failed: {e}"}
    return {"status": "ok", "message": "Ingestion completed. Check the server logs for details."}
