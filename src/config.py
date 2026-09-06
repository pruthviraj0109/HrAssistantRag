import os

from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"/ "policies"
CHROMA_DIR = BASE_DIR / "vectorstore" / "results"
EVAL_RESULTS_DIR = BASE_DIR /"evaluation" / "results"


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHROMA_COLLECTION_NAME = "hr_policies"


FIXED_CHUNK_SIZE = 500
FIXED_CHUNK_OVERLAP = 50
RECURSIVE_CHUNK_OVERLAP =50

TOP_K= 4

GROQ_API_KEY = os.getenv("GROQ_API_KEY","")
GROQ_MODEL = os.getenv("GROQ_MODEL","llama-3.1-8b-instant")


if not GROQ_API_KEY:
    raise ValueError("" \
    "GROQ_API_KEY is not found")
