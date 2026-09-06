import config
from src.document.loader import load_documents
from src.document.cleaner import clean_documents
from src.chunking.fixed_size import chunk_fixed_size
from src.chunking.recursive import chunk_recursive
from src.chunking.compare import compare_strategies
from src.retrieval.vector_store import build_vector_store


def run_ingestion():
    print("Loading documents:-:-:")
    raw_pages = load_documents(config.DATA_DIR)
    print(f"Loaded {len(raw_pages)} page / paragraph units.")

    print("Cleaning documents:-:-:")
    cleaned_pages = clean_documents(raw_pages)

    print("Chunking (fixed-size)...")
    fixed_chunks = chunk_fixed_size(
        cleaned_pages, config.FIXED_CHUNK_SIZE, config.FIXED_CHUNK_OVERLAP
    )

    print("Chunking (recursive)...")
    recursive_chunks = chunk_recursive(
        cleaned_pages, config.RECURSIVE_CHUNK_SIZE, config.RECURSIVE_CHUNK_OVERLAP
    )

    print(compare_strategies(fixed_chunks, recursive_chunks))

    print("Embedding and storing chunk in Chroma ..")
    build_vector_store(recursive_chunks)
    print("Ingestion complete. Vector store persisted at:", config.CHROMA_DIR)

    if __name__ == "__main__":
        run_ingestion()
