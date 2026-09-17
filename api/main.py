from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import Dict
from pathlib import Path
import shutil
import config

from langchain_core.messages import HumanMessage


from src.agents.rag_agent import RagAgent
from src.ingestion_pipeline import run_ingestion
from src.graph.hr_graph import build_hr_graph

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
agents_sessions: dict[tuple, dict] = {}


ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"]


class ChatRequest(BaseModel):
    domain: str = Field(..., description=f"One of: {config.SUPPORTED_DOMAINS}")
    question: str = Field(..., min_length=1, description="The user's question")


class ChatResponse(BaseModel):
    answer: str


class MultiAgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    domain: str = Field(default="hr")


class SourceRef(BaseModel):
    document: str | None = None
    page: int | None = None
    chunk_id: str | None = None


class HRAssistantRequest(BaseModel):
    message: str = Field(..., min_length=1)


class HRAssistantResponse(BaseModel):
    answer: str
    agent: str


@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.get("/domains")
def list_domains():
    return {"domains": config.SUPPORTED_DOMAINS}


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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    if request.domain not in config.SUPPORTED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain. Choose from {config.SUPPORTED_DOMAINS}",
        )

    key = (current_user.username, request.domain)
    if key not in agents_sessions:
        vectorstore_dir = config.get_vectorstore_dir(
            current_user.username, request.domain
        )
        collection_name = config.get_collection_name(
            current_user.username, request.domain
        )
        vector_store = load_vector_store(vectorstore_dir, collection_name)
        agents_sessions[key] = RagAgent(vector_store, request.domain)

    try:
        answer = agents_sessions[key].ask(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(answer=answer)


@app.post("/chat/hr-assistant", response_model=HRAssistantResponse)
def chat(
    request: HRAssistantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hr_domain = "hr"
    key = (current_user.username, hr_domain)

    if key not in agents_sessions:
        vector_store = load_vector_store(
            config.get_vectorstore_dir(current_user.username, hr_domain),
            config.get_collection_name(current_user.username, hr_domain),
        )
        rag_agent = RagAgent(vector_store, hr_domain)

        graph = build_hr_graph(
            rag_agent=rag_agent,
            db=db,
        )

        agents_sessions[key] = {
            "rag_agent": rag_agent,
            "graph": graph,
        }

    graph = agents_sessions[key]["graph"]

    config_dict = {
        "configurable": {"thread_id": f"hr-assistant-{current_user.username}"}
    }

    try:
        result = graph.invoke(
            {
                "messages":[HumanMessage(content=request.message)],
                "question": request.message,
                "user_id": current_user.id,
                "username": current_user.username,
            },
            config=config_dict,
        )
        print(result)

    except Exception as e:
        import traceback

        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        )

    return HRAssistantResponse(
        answer=result.get(
            "final_answer",
            result.get(
                "agent_response",
                "I could not process your request.",
            ),
        ),
        agent=result.get(
            "selected_agent",
            "employee_support",
        ),
    )


@app.post("/reset")
def reset_conversation(domain: str, current_user: User = Depends(get_current_user)):
    key = (current_user.username, domain)
    if key in agents_sessions:
        agents_sessions[key].memory.clear()
    return {"status": "Conversation memory cleared"}
