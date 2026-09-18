"""
memory/memory_store.py
------------------------
FEATURE 3: Session-based conversation memory.

For this beginner project, memory is kept in a simple in-memory Python
dictionary. This means:
  - Memory works while the backend server is running.
  - Memory is LOST if you restart the server (that's fine for learning
    purposes; a real production app would use a database like Redis).

Each session (identified by a "session_id" sent from the frontend) has
its own list of past messages, so different students (or browser tabs)
don't see each other's conversations.
"""

from backend.config import MEMORY_MAX_TURNS

# The main in-memory store.
# Structure:
# {
#   "session-id-1": [
#       {"role": "user", "content": "My department is CSE."},
#       {"role": "assistant", "content": "Okay, noted!"},
#       ...
#   ],
#   "session-id-2": [...],
# }
_sessions: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    """Returns the conversation history for a session (empty list if the
    session is new)."""
    return _sessions.get(session_id, [])


def add_message(session_id: str, role: str, content: str) -> None:
    """Adds a message to a session's history and trims old messages so
    memory doesn't grow forever.

    `role` should be "user" or "assistant".
    """
    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append({"role": role, "content": content})

    # Keep only the most recent MEMORY_MAX_TURNS * 2 messages (each "turn"
    # is one user message + one assistant reply).
    max_messages = MEMORY_MAX_TURNS * 2
    if len(_sessions[session_id]) > max_messages:
        _sessions[session_id] = _sessions[session_id][-max_messages:]


def reset_session(session_id: str) -> bool:
    """Clears the conversation history for a session. Returns True if a
    session existed and was cleared, False if there was nothing to
    clear."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def session_exists(session_id: str) -> bool:
    return session_id in _sessions
