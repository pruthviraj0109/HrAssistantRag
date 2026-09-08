from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Dict
from pathlib import Path
import shutil
import config
from src.agent.rag_agent import RagAgent
from src.ingestion_pipeline import run_ingestion

app = FastAPI(
    title="HR Policy Assistant Api",
    description="RAG-based API that answers HR policy questions",
    version="1.0.0",
)


agent = RagAgent()


ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"]


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's question")


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        answer = agent.ask(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error:{str(e)}")
    return ChatResponse(answer=answer)


@app.post("/reset")
def reset_conversation():
    agent.memory.clear()
    return {"status": "Conversation memory cleared"}


@app.post("/upload")
def upload_document(file: UploadFile = File(...)):

    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = config.DATA_DIR / file.filename

    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {ste(e)}")
    finally:
        file.file.close()
    try:
        run_ingestion()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return {"status": "Upload and ingested", "filename": file.filename}
