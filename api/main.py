from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from langchain_core.callbacks import (
    BaseCallbackHandler,
    get_usage_metadata_callback,
)
from pydantic import BaseModel, Field
from pathlib import Path
import config
from time import perf_counter
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
    domain: str = Field(
        ...,
        description=f"One of: {config.SUPPORTED_DOMAINS}",
    )
    question: str = Field(
        ...,
        min_length=1,
        description="The user's question",
    )


class RunMetrics(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    model: str | None = None
    tool_calls: int = 0
    tools_used: list[str] = Field(default_factory=list)
    llm_calls: int = 0


class ChatResponse(BaseModel):
    answer: str
    metrics: RunMetrics | None = None


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
    metrics: RunMetrics | None = None


class ExecutionMetricsCallback(BaseCallbackHandler):
    def __init__(self):
        self.llm_calls = 0
        self.tool_calls = 0
        self.tools_used = []
        self.models = []

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.llm_calls += 1

        model_name = None

        if isinstance(serialized, dict):
            kwargs_data = serialized.get("kwargs", {})

            model_name = (
                kwargs_data.get("model")
                or kwargs_data.get("model_name")
                or kwargs_data.get("model_id")
            )

            if not model_name:
                model_name = serialized.get("name")

        if model_name and model_name not in self.models:
            self.models.append(model_name)

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.llm_calls += 1

        model_name = None

        if isinstance(serialized, dict):
            kwargs_data = serialized.get("kwargs", {})

            model_name = (
                kwargs_data.get("model")
                or kwargs_data.get("model_name")
                or kwargs_data.get("model_id")
            )

            if not model_name:
                model_name = serialized.get("name")

        if model_name and model_name not in self.models:
            self.models.append(model_name)

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.tool_calls += 1

        tool_name = None

        if isinstance(serialized, dict):
            tool_name = (
                serialized.get("name")
                or serialized.get("id")
                or serialized.get("kwargs", {}).get("name")
            )

        if tool_name and tool_name not in self.tools_used:
            self.tools_used.append(tool_name)


def _collect_metrics(
    usage: dict,
    latency_ms: int,
    execution_metrics: ExecutionMetricsCallback,
) -> RunMetrics:

    metrics = RunMetrics(
        latency_ms=latency_ms,
        llm_calls=execution_metrics.llm_calls,
        tool_calls=execution_metrics.tool_calls,
        tools_used=execution_metrics.tools_used,
    )

    for model_name, usage_data in (usage or {}).items():

        if metrics.model is None:
            metrics.model = model_name

        metrics.input_tokens += usage_data.get(
            "input_tokens",
            0,
        )

        metrics.output_tokens += usage_data.get(
            "output_tokens",
            0,
        )

        metrics.total_tokens += usage_data.get(
            "total_tokens",
            0,
        )

    if metrics.model is None and execution_metrics.models:
        metrics.model = execution_metrics.models[0]

    return metrics


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

    if not any(
        suffix_check.endswith(ext)
        for ext in ALLOWED_EXTENSIONS
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    file_bytes = file.file.read()
    file.file.close()

    try:
        result = run_ingestion(
            current_user.username,
            domain,
            file_bytes,
            file.filename,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        )

    agents_sessions.pop(
        (current_user.username, domain),
        None,
    )

    return {
        "status": "processed and embedded",
        "result": result,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):

    if request.domain not in config.SUPPORTED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain. Choose from {config.SUPPORTED_DOMAINS}",
        )

    key = (
        current_user.username,
        request.domain,
    )

    if key not in agents_sessions:

        vectorstore_dir = config.get_vectorstore_dir(
            current_user.username,
            request.domain,
        )

        collection_name = config.get_collection_name(
            current_user.username,
            request.domain,
        )

        vector_store = load_vector_store(
            vectorstore_dir,
            collection_name,
        )

        agents_sessions[key] = RagAgent(
            vector_store,
            request.domain,
        )

    try:
        answer = agents_sessions[key].ask(
            request.question
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        )

    return ChatResponse(
        answer=answer
    )


@app.post(
    "/chat/hr-assistant",
    response_model=HRAssistantResponse,
)
def chat_hr_assistant(
    request: HRAssistantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    hr_domain = "hr"

    key = (
        current_user.username,
        hr_domain,
    )

    if key not in agents_sessions:

        vector_store = load_vector_store(
            config.get_vectorstore_dir(
                current_user.username,
                hr_domain,
            ),
            config.get_collection_name(
                current_user.username,
                hr_domain,
            ),
        )

        rag_agent = RagAgent(
            vector_store,
            hr_domain,
        )

        graph = build_hr_graph(
            rag_agent=rag_agent,
        )

        agents_sessions[key] = {
            "rag_agent": rag_agent,
            "graph": graph,
        }

    graph = agents_sessions[key]["graph"]

    config_dict = {
        "configurable": {
            "thread_id": f"hr-assistant-{current_user.username}",
            "db": db,
        },
        "metadata": {
            "user_id": current_user.id,
            "username": current_user.username,
            "domain": hr_domain,
        },
        "tags": [
            "hr-assistant",
            "multi-agent",
        ],
        "run_name": f"hr-chat-{current_user.username}",
    }

    execution_metrics = ExecutionMetricsCallback()

    try:

        with get_usage_metadata_callback() as usage_callback:

            started = perf_counter()

            graph_result = graph.invoke(
                {
                    "messages": [
                        HumanMessage(
                            content=request.message
                        )
                    ],
                    "question": request.message,
                    "user_id": current_user.id,
                    "username": current_user.username,
                },
                config={
                    **config_dict,
                    "callbacks": [
                        execution_metrics
                    ],
                },
            )

            latency_ms = int(
                (perf_counter() - started) * 1000
            )

            usage = usage_callback.usage_metadata

            print(graph_result)

            print("USAGE METADATA:")
            print(usage)

    except Exception as e:

        import traceback

        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        )

    metrics = _collect_metrics(
        usage=usage,
        latency_ms=latency_ms,
        execution_metrics=execution_metrics,
    )

    print(
        f"[metrics] "
        f"{current_user.username} · "
        f"{metrics.total_tokens} tokens · "
        f"{metrics.latency_ms}ms · "
        f"llm_calls={metrics.llm_calls} · "
        f"tool_calls={metrics.tool_calls} · "
        f"tools={metrics.tools_used}"
    )

    return HRAssistantResponse(
        answer=graph_result.get(
            "final_answer",
            graph_result.get(
                "agent_response",
                "I could not process your request.",
            ),
        ),
        agent=graph_result.get(
            "selected_agent",
            "employee_support",
        ),
        metrics=metrics,
    )


@app.post("/reset")
def reset_conversation(
    domain: str,
    current_user: User = Depends(get_current_user),
):

    key = (
        current_user.username,
        domain,
    )

    if key in agents_sessions:

        session = agents_sessions[key]

        if isinstance(session, dict):

            graph = session.get("graph")

            if graph is not None:
                pass

        elif hasattr(session, "memory"):

            session.memory.clear()

    return {
        "status": "Conversation memory cleared"
    }