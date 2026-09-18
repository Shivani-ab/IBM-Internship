"""
tools/notice_search.py
------------------------
TOOL 1: Notice / Document Search Tool.

This tool lets Gemini search the ingested college documents by KEYWORD
(rather than by meaning/embedding search, which is what the main RAG
pipeline already does). This is useful for direct requests like:
"Show me exam-related notices" or "Find documents about attendance",
where the student wants to know WHICH documents exist / mention a topic,
not a synthesized answer.

It reuses the same ChromaDB collection created during ingestion.
"""

from backend.rag.retriever import _get_collection


def search_notices(keyword: str, max_results: int = 5):
    """Searches all stored document chunks for a keyword and returns a
    summary grouped by filename.

    Returns a dict:
        {
            "keyword": "exam",
            "found": True,
            "results": [
                {"filename": "Notice_Exam_Schedule.pdf", "page": 1,
                 "snippet": "..."},
                ...
            ]
        }
    """
    keyword = (keyword or "").strip()
    if not keyword:
        return {"keyword": keyword, "found": False, "results": []}

    collection = _get_collection()
    if collection is None:
        return {"keyword": keyword, "found": False, "results": [],
                 "error": "No documents have been ingested yet."}

    try:
        # Pull all chunks (fine for a small beginner project) and filter
        # in Python. This keeps the tool simple and easy to understand.
        all_data = collection.get(include=["documents", "metadatas"])
    except Exception as e:
        return {"keyword": keyword, "found": False, "results": [],
                 "error": f"Search failed: {e}"}

    documents = all_data.get("documents", [])
    metadatas = all_data.get("metadatas", [])

    keyword_lower = keyword.lower()
    matches = []

    for text, metadata in zip(documents, metadatas):
        if keyword_lower in text.lower():
            snippet = text.strip().replace("\n", " ")
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            matches.append({
                "filename": metadata.get("filename", "unknown"),
                "page": metadata.get("page", -1),
                "snippet": snippet,
            })
        if len(matches) >= max_results:
            break

    return {
        "keyword": keyword,
        "found": len(matches) > 0,
        "results": matches,
    }
