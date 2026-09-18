"""
chat/assistant.py
-----------------

Student Support Assistant

Architecture:

Student Question
       |
       v
     RAG
       |
       v
Python Tool Router
       |
       +---- notice_search
       |
       +---- college_info
       |
       v
   Gemini
       |
       v
 Final Answer

Important:
Gemini itself does NOT perform function calling here.
Python executes the tools directly.

This avoids Gemini 3 thought_signature errors.
"""

import re

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.rag.retriever import (
    retrieve_relevant_chunks,
    is_knowledge_base_ready,
)
from backend.tools.notice_search import search_notices
from backend.tools.college_info import get_college_info
from backend.memory import memory_store


# =========================================================
# GEMINI CLIENT
# =========================================================

_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# CONSTANTS
# =========================================================

NOT_FOUND_MESSAGE = (
    "I could not find this information in the available "
    "college documents."
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are the Student Support Assistant.

You help students with college-related questions.

STRICT RULES:

1. Answer only using the information provided in:
   - Retrieved college document excerpts
   - Tool results
   - Conversation history for context only

2. NEVER invent or guess:
   - credits
   - subjects
   - regulations
   - fees
   - dates
   - attendance rules
   - examination rules
   - college procedures
   - contact information
   - any other college-specific information

3. If the information is not available in the provided
   documents or tool results, reply exactly:

   I could not find this information in the available college documents.

4. If information comes from a college document, mention
   the source.

5. If tool information is marked as SAMPLE DATA, clearly
   tell the student that it is sample data and should be
   verified with the college administration.

6. Keep answers simple, short and student-friendly.

7. Do not make assumptions.

8. If the student asks a specific factual question such as
   "How many credits are there for semester 7?",
   give the exact number only if it is present in the
   supplied information.

9. If the information is missing, use the exact
   NOT FOUND response.
"""


# =========================================================
# TOOL 1 - NOTICE SEARCH
# =========================================================

def run_notice_search(keyword: str) -> dict:
    """
    Python-side notice search tool.
    """

    try:

        result = search_notices(
            keyword
        )

        return result

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# TOOL 2 - COLLEGE INFORMATION
# =========================================================

def run_college_info(topic: str) -> dict:
    """
    Python-side college information tool.
    """

    try:

        result = get_college_info(
            topic
        )

        return result

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# TOOL ROUTER
# =========================================================

def _should_search_notice(
    message: str,
) -> bool:
    """
    Decide whether the student is explicitly asking
    to search for notices/documents.

    We intentionally do NOT let Gemini decide this.
    """

    text = message.lower().strip()

    notice_words = [
        "notice",
        "notices",
        "announcement",
        "announcements",
        "circular",
        "circulars",
        "find notice",
        "show notice",
        "search notice",
        "find the notice",
        "show the notice",
        "search the notice",
        "find document",
        "show document",
        "search document",
    ]

    for word in notice_words:

        if word in text:
            return True

    return False


def _should_get_college_info(
    message: str,
) -> bool:
    """
    Decide whether structured college information
    should be retrieved.
    """

    text = message.lower().strip()

    keywords = [
        "working hours",
        "office hours",
        "college hours",
        "department contact",
        "contact number",
        "exam cell",
        "student office",
        "office contact",
    ]

    for word in keywords:

        if word in text:
            return True

    return False


# =========================================================
# RAG FORMATTER
# =========================================================

def _format_retrieved_chunks(
    chunks: list[dict],
) -> str:
    """
    Convert ChromaDB results into readable text.
    """

    if not chunks:

        return (
            "No relevant college document excerpts "
            "were found."
        )

    lines = []

    for i, chunk in enumerate(
        chunks,
        start=1
    ):

        filename = chunk.get(
            "filename",
            "Unknown source"
        )

        page = chunk.get(
            "page"
        )

        text = chunk.get(
            "text",
            ""
        )

        if page and page != -1:

            source = (
                f"{filename}, Page {page}"
            )

        else:

            source = filename

        lines.append(
            f"[Excerpt {i} - Source: {source}]\n"
            f"{text}"
        )

    return "\n\n".join(lines)


# =========================================================
# SOURCE EXTRACTION
# =========================================================

def _extract_sources(
    chunks: list[dict],
) -> list[dict]:
    """
    Remove duplicate sources.
    """

    seen = set()

    sources = []

    for chunk in chunks:

        filename = chunk.get(
            "filename",
            "Unknown"
        )

        page = chunk.get(
            "page"
        )

        if page == -1:

            page = None

        key = (
            filename,
            page
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append(
            {
                "filename": filename,
                "page": page,
            }
        )

    return sources


def _find_subject_code(
    message: str,
    chunks: list[dict],
) -> tuple[str, dict] | None:
    """Return an exact course code when the document contains one."""

    question = message.lower()
    if "subject code" not in question and "course code" not in question:
        return None

    subject_match = re.search(
        r"(?:subject|course)\s+code\s+(?:of|for)\s+(.+?)(?:\?|$)",
        question,
    )
    if not subject_match:
        return None

    subject = re.sub(r"\s+", " ", subject_match.group(1)).strip()
    if not subject:
        return None

    for chunk in chunks:
        normalized_text = re.sub(r"\s+", " ", chunk.get("text", ""))
        code_match = re.search(
            rf"\b([A-Z]{{2,5}}\d{{3,4}})\s+{re.escape(subject)}\b",
            normalized_text,
            re.IGNORECASE,
        )
        if code_match:
            return code_match.group(1).upper(), chunk

    return None


# =========================================================
# MEMORY
# =========================================================

def _history_to_gemini_contents(
    history: list[dict],
) -> list[types.Content]:
    """
    Convert normal text memory into Gemini content.

    No previous function calls are stored here.
    """

    contents = []

    for msg in history:

        role = (
            "model"
            if msg["role"] == "assistant"
            else "user"
        )

        contents.append(
            types.Content(
                role=role,
                parts=[
                    types.Part.from_text(
                        text=msg["content"]
                    )
                ],
            )
        )

    return contents


# =========================================================
# TOOL RESULT FORMATTER
# =========================================================

def _format_tool_result(
    tool_name: str,
    result: dict,
) -> str:
    """
    Convert Python tool output into text that Gemini
    can understand.
    """

    return (
        f"\n\n===== TOOL RESULT: {tool_name} =====\n"
        f"{result}\n"
        f"===== END TOOL RESULT =====\n"
    )


# =========================================================
# MAIN FUNCTION
# =========================================================

def get_answer(
    session_id: str,
    message: str,
) -> dict:
    """
    Main function used by FastAPI /chat.
    """

    # -----------------------------------------------------
    # Clean message
    # -----------------------------------------------------

    message = (
        message or ""
    ).strip()

    if not message:

        return {
            "answer": "Please enter a question.",
            "sources": [],
        }

    # =====================================================
    # STEP 1 - RAG
    # =====================================================

    retrieved_chunks = []

    if is_knowledge_base_ready():

        try:

            retrieved_chunks = (
                retrieve_relevant_chunks(
                    message
                )
            )

        except Exception:

            retrieved_chunks = []

    subject_code_match = _find_subject_code(
        message,
        retrieved_chunks,
    )

    if (
        subject_code_match is None
        and (
            "subject code" in message.lower()
            or "course code" in message.lower()
        )
        and is_knowledge_base_ready()
    ):
        retrieved_chunks = retrieve_relevant_chunks(
            message,
            top_k=10,
        )
        subject_code_match = _find_subject_code(
            message,
            retrieved_chunks,
        )

    if subject_code_match is not None:
        subject_code, source_chunk = subject_code_match
        source = source_chunk.get("filename", "college document")
        page = source_chunk.get("page", -1)
        page_reference = f", page {page}" if page != -1 else ""
        answer = (
            f"The subject code is {subject_code}. "
            f"Source: {source}{page_reference}."
        )
        memory_store.add_message(session_id, "user", message)
        memory_store.add_message(session_id, "assistant", answer)
        return {
            "answer": answer,
            "sources": _extract_sources([source_chunk]),
        }

    retrieved_text = (
        _format_retrieved_chunks(
            retrieved_chunks
        )
    )

    # =====================================================
    # STEP 2 - PYTHON TOOL ROUTING
    # =====================================================

    tool_results = ""

    tool_was_used = False

    # -----------------------------------------------------
    # Notice Search
    # -----------------------------------------------------

    if _should_search_notice(message):

        notice_result = run_notice_search(
            message
        )

        tool_results += _format_tool_result(
            "notice_search",
            notice_result,
        )

        tool_was_used = True

    # -----------------------------------------------------
    # College Info
    # -----------------------------------------------------

    if _should_get_college_info(message):

        college_result = run_college_info(
            message
        )

        tool_results += _format_tool_result(
            "college_info",
            college_result,
        )

        tool_was_used = True

    # =====================================================
    # STEP 3 - MEMORY
    # =====================================================

    history = (
        memory_store.get_history(
            session_id
        )
    )

    contents = (
        _history_to_gemini_contents(
            history
        )
    )

    # =====================================================
    # STEP 4 - BUILD PROMPT
    # =====================================================

    user_prompt = f"""
RETRIEVED COLLEGE DOCUMENT EXCERPTS:

{retrieved_text}

{tool_results}

STUDENT QUESTION:

{message}

IMPORTANT:

Answer ONLY from the information above.

If the answer is not available in the retrieved documents
or tool results, reply exactly:

I could not find this information in the available college documents.
"""

    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=user_prompt
                )
            ],
        )
    )

    # =====================================================
    # STEP 5 - GEMINI CONFIG
    # =====================================================

    # IMPORTANT:
    #
    # There is NO "tools=" here.
    #
    # Therefore Gemini will NOT perform function calling.
    # This avoids the Gemini 3 thought_signature problem.
    #

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
    )

    # =====================================================
    # STEP 6 - CALL GEMINI
    # =====================================================

    try:

        response = (
            _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            )
        )

    except genai_errors.ClientError as e:

        error_text = str(e)

        if (
            "API key" in error_text
            or "API_KEY" in error_text
            or "401" in error_text
            or "403" in error_text
        ):

            raise RuntimeError(
                "The Gemini API key was rejected. "
                "Please check GEMINI_API_KEY in your .env file."
            )

        raise RuntimeError(
            f"Gemini API error: {e}"
        )

    except genai_errors.ServerError as e:

        raise RuntimeError(
            f"Gemini API server error: {e}"
        )

    except Exception as e:

        raise RuntimeError(
            f"Gemini API error: {e}"
        )

    # =====================================================
    # STEP 7 - GET RESPONSE
    # =====================================================

    try:

        answer_text = (
            response.text or ""
        ).strip()

    except Exception:

        answer_text = ""

    if not answer_text:

        answer_text = NOT_FOUND_MESSAGE

    # =====================================================
    # STEP 8 - SOURCES
    # =====================================================

    sources = []

    if (
        NOT_FOUND_MESSAGE not in answer_text
        and retrieved_chunks
    ):

        sources = _extract_sources(
            retrieved_chunks
        )

    # =====================================================
    # STEP 9 - MEMORY
    # =====================================================

    memory_store.add_message(
        session_id,
        "user",
        message,
    )

    memory_store.add_message(
        session_id,
        "assistant",
        answer_text,
    )

    # =====================================================
    # STEP 10 - RETURN
    # =====================================================

    return {
        "answer": answer_text,
        "sources": sources,
    }