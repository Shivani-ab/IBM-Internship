"""
rag/ingest.py
--------------
This script reads all PDF and TXT files from backend/data/documents,
splits them into small chunks, creates embeddings for each chunk, and
stores everything inside ChromaDB (a local vector database saved on disk
in the chroma_db/ folder).

You need to run this script:
  1. The first time you set up the project.
  2. Every time you add, remove, or change a document.

How to run it (from the project root folder, with your virtual
environment activated):

    python -m backend.rag.ingest

Beginner explanation of what "embeddings" are:
An embedding is a list of numbers that represents the MEANING of a piece
of text. Texts with similar meaning end up with similar numbers. This is
what lets us search "by meaning" instead of just matching exact words.
"""

import os
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

# Make sure we can import backend.config whether this file is run directly
# or as a module (python -m backend.rag.ingest).
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.config import (
    DOCUMENTS_DIR,
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
)

# Chunking settings.
# CHUNK_SIZE = number of characters per chunk.
# CHUNK_OVERLAP = how many characters each chunk repeats from the previous
# chunk, so we don't cut a sentence/idea in half at a boundary.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def read_txt_file(file_path: Path) -> list[tuple[str, int | None]]:
    """Reads a .txt file and returns a list of (text, page_number) tuples.
    Plain text files don't have "pages", so page_number is None."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return [(text, None)]
    except Exception as e:
        print(f"  [WARNING] Could not read TXT file {file_path.name}: {e}")
        return []


def read_pdf_file(file_path: Path) -> list[tuple[str, int | None]]:
    """Reads a .pdf file and returns a list of (text, page_number) tuples,
    one entry per page. This lets us tell the student which page an answer
    came from."""
    pages_text = []
    try:
        reader = PdfReader(str(file_path))
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as e:
                print(f"  [WARNING] Could not extract page {page_number} "
                      f"of {file_path.name}: {e}")
                text = ""
            if text.strip():
                pages_text.append((text, page_number))
    except Exception as e:
        print(f"  [WARNING] Could not open PDF file {file_path.name}: {e}")
    return pages_text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Splits a long piece of text into overlapping chunks of roughly
    `chunk_size` characters. Overlap helps preserve context across chunk
    boundaries."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # Move the window forward, leaving `overlap` characters of
        # repetition so context is not lost between chunks.
        start += chunk_size - overlap

    return chunks


def build_chunks_for_file(file_path: Path):
    """Returns a list of dicts, each representing one chunk with its text
    and metadata (filename, doc type, page number)."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        raw_sections = read_pdf_file(file_path)
        doc_type = "pdf"
    elif suffix == ".txt":
        raw_sections = read_txt_file(file_path)
        doc_type = "txt"
    else:
        return []

    results = []
    for text, page_number in raw_sections:
        for chunk in chunk_text(text):
            results.append({
                "text": chunk,
                "filename": file_path.name,
                "doc_type": doc_type,
                "page": page_number if page_number is not None else -1,
            })
    return results


def run_ingestion():
    project_root = Path(__file__).resolve().parents[2]
    documents_path = project_root / DOCUMENTS_DIR
    chroma_path = project_root / CHROMA_DB_DIR

    print("=" * 60)
    print("Student Support Assistant - Document Ingestion")
    print("=" * 60)
    print(f"Reading documents from: {documents_path}")

    if not documents_path.exists():
        print(f"[ERROR] Documents folder not found: {documents_path}")
        print("Create the folder and add PDF/TXT files, then run this "
              "script again.")
        return

    supported_files = [
        f for f in documents_path.iterdir()
        if f.is_file() and f.suffix.lower() in (".pdf", ".txt")
    ]

    if not supported_files:
        print("[WARNING] No PDF or TXT files found in the documents "
              "folder.")
        print("Add some files there and run this script again. The "
              "assistant will not be able to answer document-based "
              "questions until you do.")
        return

    print(f"Found {len(supported_files)} file(s): "
          f"{', '.join(f.name for f in supported_files)}")

    # Build all chunks from all files first.
    all_chunks = []
    for file_path in supported_files:
        print(f"Processing: {file_path.name}")
        file_chunks = build_chunks_for_file(file_path)
        print(f"  -> {len(file_chunks)} chunk(s) created")
        all_chunks.extend(file_chunks)

    if not all_chunks:
        print("[WARNING] No text could be extracted from any document. "
              "PDFs that are scanned images (no selectable text) cannot "
              "be read this way.")
        return

    # Connect to (or create) the local ChromaDB database on disk.
    print(f"\nConnecting to ChromaDB at: {chroma_path}")
    client = chromadb.PersistentClient(path=str(chroma_path))

    # ChromaDB's default embedding function downloads a small local model
    # (all-MiniLM-L6-v2, run via ONNX) the first time it is used. This
    # keeps things simple: no external embedding API or key is needed.
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    # Reset the collection each time we ingest, so removed/changed
    # documents don't leave stale chunks behind.
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass  # Collection didn't exist yet; that's fine.

    collection = client.create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    print(f"Embedding and storing {len(all_chunks)} chunk(s)... "
          f"(this may take a little while the first time)")

    # ChromaDB needs a unique ID per chunk, plus the text, and metadata.
    ids = [f"chunk-{i}" for i in range(len(all_chunks))]
    documents = [c["text"] for c in all_chunks]
    metadatas = [
        {
            "filename": c["filename"],
            "doc_type": c["doc_type"],
            "page": c["page"],
        }
        for c in all_chunks
    ]

    # Add in batches to avoid overwhelming memory on very large document
    # sets. 100 at a time is safe for a beginner project.
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    print("\n[SUCCESS] Ingestion complete!")
    print(f"Total chunks stored: {len(all_chunks)}")
    print("You can now start the backend server and ask questions.")


if __name__ == "__main__":
    run_ingestion()
