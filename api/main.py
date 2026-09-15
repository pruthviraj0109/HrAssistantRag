from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import Dict
from pathlib import Path
import shutil
import config
from src.agent.rag_agent import RagAgent
from src.ingestion_pipeline import run_ingestion

from src.retrieval.vector_store import load_vector_store
from sqlalchemy.orm import Session

from db.database import Base, engine, get_db
from db.models import User
from auth.routes import router as auth_router
from auth.dependencies import get_current_user

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Mulit-Domain RAG Assistant API",
    version="1.0.0",
)

app.include_router(auth_router, tags=["auth"])
agents_sessions: dict[tuple, RagAgent] = {}


# agent = RagAgent()


ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"]


class ChatRequest(BaseModel):
    domain: str = Field(..., description=f"One of: {config.SUPPORTED_DOMAINS}")
    question: str = Field(..., min_length=1, description="The user's question")


class ChatResponse(BaseModel):
    answer: str


@app.get("/domains")
def list_domains():
    return {"domains": config.SUPPORTED_DOMAINS}


@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.post("/upload")
def upload_document(
    domain: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if domain not in config.SUPPORTED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain. Choose from {config.SUPPORTED_DOMAINS}",
        )

    suffix_check = file.filename.lower()

    if not any(suffix_check.endswith(ext) for ext in config.ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type . Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    file_bytes = file.file.read()
    file.file.close()

    try:
        result = run_ingestion(current_user.username, domain, file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    agents_sessions.pop((current_user.username, domain), None)

    return {
        "status": "processed and embedded ",
        # "filename": result["filename"],
        "result": result,
    }


@app.post("/chat")
def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    if request.domain not in config.SUPPORTED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain. Choose from {config.SUPPORTED_DOMAINS}",
        )

    key = (current_user.username, request.domain)

    if key not in agents_sessions:
        vectorestore_dir = config.get_vectorstore_dir(
            current_user.username, request.domain
        )
        collection_name = config.get_collection_name(
            current_user.username, request.domain
        )
        vector_store = load_vector_store(vectorestore_dir, collection_name)
        agents_sessions[key] = RagAgent(vector_store, request.domain)

    try:
        answer = agents_sessions[key].ask(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error:{str(e)}")
    return {"answer": answer}


@app.post("/reset")
def reset_conversation(domain: str, current_user: User = Depends(get_current_user)):
    key = (current_user.username, domain)
    if key in agents_sessions:
        agents_sessions[key].memory.clear()
    return {"status": "Conversation memory cleared"}
