"""
config.py
---------
Loads all configuration values (like the Gemini API key) from the .env file.

Beginner note:
We NEVER write the API key directly in code. Instead, it is stored in a
separate file called ".env" (in the project's root folder) and loaded here
using the python-dotenv library. This keeps the key private and out of
version control (see .gitignore).
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment.
# This looks for a file named ".env" in the current working directory
# (which will be the project root when you run "uvicorn backend.main:app").
load_dotenv()

# The Gemini API key. This will be None if the .env file is missing or
# the key was not set. We check for this in main.py and give a friendly
# error message instead of crashing with a confusing traceback.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# The Gemini model to use for chat responses.
# gemini-2.5-flash is fast, cost-effective, and supports tool/function
# calling, which is what this project needs.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Folder where uploaded college documents (PDF/TXT) live.
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "backend/data/documents")

# Folder where ChromaDB will persist its data (so you don't have to
# re-ingest documents every time you restart the server).
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "chroma_db")

# Name of the ChromaDB "collection" (a bit like a table name).
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "college_documents")

# How many chunks to retrieve from ChromaDB for each question.
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))

# How many past messages (user + assistant) to keep in memory per session.
MEMORY_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "10"))


def is_api_key_configured() -> bool:
    """Returns True only if a non-empty API key was found."""
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip())
