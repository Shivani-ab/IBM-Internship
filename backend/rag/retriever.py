"""
rag/retriever.py
------------------
Handles searching ChromaDB for the chunks most relevant to a student's
question. This is the "Retrieval" part of Retrieval Augmented Generation
(RAG).
"""

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from backend.config import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, RAG_TOP_K

_project_root = Path(__file__).resolve().parents[2]
_chroma_path = _project_root / CHROMA_DB_DIR

# These are created once and reused for every request (faster, and avoids
# re-loading the embedding model on every single question).
_client = None
_collection = None


def _get_collection():
    """Lazily connects to ChromaDB and fetches the collection. Returns
    None if the collection does not exist yet (i.e. ingestion has not
    been run)."""
    global _client, _collection

    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(path=str(_chroma_path))
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    try:
        _collection = _client.get_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_fn,
        )
    except Exception:
        # Collection doesn't exist yet -> ingestion was never run.
        _collection = None

    return _collection


def is_knowledge_base_ready() -> bool:
    """Returns True if there is at least one document chunk stored."""
    collection = _get_collection()
    if collection is None:
        return False
    try:
        return collection.count() > 0
    except Exception:
        return False


def retrieve_relevant_chunks(question: str, top_k: int = RAG_TOP_K):
    """Searches ChromaDB for the chunks most relevant to `question`.

    Returns a list of dicts:
        {
            "text": "...",
            "filename": "Regulation.pdf",
            "doc_type": "pdf",
            "page": 12,
        }
    Returns an empty list if the knowledge base is empty or a search
    error occurs (the caller should handle this gracefully rather than
    crashing).
    """
    collection = _get_collection()
    if collection is None:
        return []

    question = (question or "").strip()
    if not question:
        return []

    try:
        results = collection.query(
            query_texts=[question],
            n_results=top_k,
        )
    except Exception as e:
        print(f"[ERROR] ChromaDB query failed: {e}")
        return []

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for text, metadata in zip(documents, metadatas):
        chunks.append({
            "text": text,
            "filename": metadata.get("filename", "unknown"),
            "doc_type": metadata.get("doc_type", "unknown"),
            "page": metadata.get("page", -1),
        })

    return chunks
