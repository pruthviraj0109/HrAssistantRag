import os
from pathlib import Path
import re
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_ROOT = BASE_DIR / "data"
VECTORSTORE_ROOT = BASE_DIR / "vectorstore"
EVAL_RESULTS_DIR = BASE_DIR / "evaluation" / "results"


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHROMA_COLLECTION_NAME = "hr_policies"


FIXED_CHUNK_SIZE = 500
FIXED_CHUNK_OVERLAP = 50
RECURSIVE_CHUNK_SIZE = 500
RECURSIVE_CHUNK_OVERLAP = 50

TOP_K = 5


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not found")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")


SUPPORTED_DOMAINS = ["hr", "healthcare", "banking", "news_media", "customer_support","government_schemes"]

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def get_data_dir(username: str, domain: str) -> Path:
    path = DATA_ROOT / username / domain
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_vectorstore_dir(username: str, domain: str) -> Path:
    path = VECTORSTORE_ROOT / username / domain
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_collection_name(username: str, domain: str) -> str:
    safe_username = re.sub(r"[^a-zA-Z0-9._-]", "_", username)
    safe_username = safe_username.strip("._-")  # trim leading/trailing invalid edge chars

    collection_name = f"{safe_username}__{domain}"

    # Chroma also requires the name to start and end with an alphanumeric char
    collection_name = collection_name.strip("._-")

    if len(collection_name) < 3:
        collection_name = f"user_{collection_name}"

    return collection_name
