# Student Support Assistant

An AI-powered chat assistant that helps college students get answers about
**regulations, syllabus, FAQs, notices, and procedures** — built for the
Naan Mudhalvan program to demonstrate three core AI capabilities:

1. **RAG (Retrieval Augmented Generation)** — answers are grounded in your
   actual uploaded college documents, not made up.
2. **Tools** — the assistant can search notices and look up structured
   college information on demand.
3. **Memory** — the assistant remembers context within a conversation
   (e.g. "my department is CSE" → later "what subjects do I have?").

This README explains everything from scratch. You do **not** need prior
experience with Python, FastAPI, RAG, ChromaDB, or APIs — every step is
spelled out.

---

## 1. What This Project Does

A student opens a simple chat webpage, types a question like *"What is the
attendance requirement?"*, and the assistant:

1. Searches the college documents you uploaded (PDF/TXT) for relevant
   passages (this is the "Retrieval" step).
2. Sends those passages, plus the question, to Gemini (Google's AI
   model), which writes an answer using **only** that information (this is
   the "Generation" step — together, "RAG").
3. If needed, Gemini can call one of two **tools**:
   - **Notice Search Tool** — searches documents by keyword (e.g. "find
     notices about exams").
   - **College Information Tool** — looks up structured facts like office
     hours or department contacts.
4. Remembers the last several messages of the conversation, so follow-up
   questions make sense.
5. If the answer isn't in the documents, it clearly says:
   > "I could not find this information in the available college documents."

---

## 2. Features

- ✅ Full RAG pipeline: PDF/TXT ingestion → chunking → embeddings → ChromaDB → retrieval
- ✅ Source citations (filename + page number) shown with every answer
- ✅ Two working tools (notice search, college info) using Gemini's native function calling
- ✅ Session-based conversation memory (in-memory Python dictionary)
- ✅ Clean, responsive chat UI (HTML/CSS/JS only — no frameworks)
- ✅ Friendly error handling for missing keys, empty documents, bad input, etc.
- ✅ Sample document included so you can test immediately
- ✅ API key never touches the frontend or gets hardcoded

---

## 3. Architecture

```
 ┌────────────┐        HTTP (fetch)        ┌─────────────────────┐
 │  Frontend  │  ───────────────────────▶  │   FastAPI Backend    │
 │ (HTML/CSS/ │  ◀───────────────────────  │     (main.py)         │
 │    JS)     │        JSON response        └──────────┬───────────┘
 └────────────┘                                         │
                                                          ▼
                                          ┌───────────────────────────┐
                                          │  chat/assistant.py         │
                                          │  (orchestrator)             │
                                          └───┬─────────┬─────────┬────┘
                                              │         │         │
                             ┌────────────────┘         │         └───────────────┐
                             ▼                           ▼                         ▼
                    ┌─────────────────┐        ┌──────────────────┐     ┌────────────────────┐
                    │  rag/retriever   │        │  memory_store     │     │  Gemini API          │
                    │  (ChromaDB query)│        │  (per-session dict)│     │  (with 2 tools)       │
                    └────────┬─────────┘        └──────────────────┘     └──────────┬─────────┘
                             │                                                        │
                             ▼                                                        ▼
                    ┌─────────────────┐                                   ┌────────────────────┐
                    │   ChromaDB        │                                   │ tools/notice_search  │
                    │  (chroma_db/)      │                                   │ tools/college_info    │
                    └────────┬─────────┘                                   └────────────────────┘
                             ▲
                             │ (ingestion, run once / when docs change)
                    ┌─────────────────┐
                    │  rag/ingest.py    │
                    │  reads PDFs/TXTs   │
                    │  from data/documents│
                    └─────────────────┘
```

---

## 4. Technologies Used

| Layer      | Technology                                   |
|------------|-----------------------------------------------|
| Backend    | Python 3.10+, FastAPI, Uvicorn                 |
| AI Model   | Google Gemini API (`google-genai` Python SDK)  |
| RAG        | ChromaDB (vector database), pypdf (PDF text)   |
| Embeddings | ChromaDB's built-in local embedding model      |
| Frontend   | HTML, CSS, JavaScript (no frameworks)          |
| Config     | python-dotenv (`.env` file)                     |

---

## 5. Folder Structure

```
student-support-assistant/
│
├── backend/
│   ├── main.py                 # FastAPI app & endpoints
│   ├── config.py                # Loads settings from .env
│   ├── requirements.txt         # Python packages needed
│   │
│   ├── rag/
│   │   ├── ingest.py             # Reads docs, creates embeddings, stores in ChromaDB
│   │   └── retriever.py          # Searches ChromaDB for relevant chunks
│   │
│   ├── tools/
│   │   ├── notice_search.py      # Tool 1: keyword search over documents
│   │   └── college_info.py       # Tool 2: structured college info (sample data)
│   │
│   ├── memory/
│   │   └── memory_store.py       # In-memory per-session conversation history
│   │
│   ├── chat/
│   │   └── assistant.py          # Orchestrates RAG + Tools + Memory + Gemini
│   │
│   └── data/
│       └── documents/            # <-- put your PDF/TXT college documents here
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── chroma_db/                    # ChromaDB's local database files (auto-created)
│
├── .env                          # Your real API key (you create this, not committed)
├── .env.example                  # Template showing what .env should contain
├── .gitignore
└── README.md
```

---

## 6. Prerequisites (Install These First)

1. **Python 3.10 or newer** — download from https://www.python.org/downloads/
   During installation, check the box **"Add Python to PATH"**.
2. **VS Code** — download from https://code.visualstudio.com/
3. A **Google Gemini API key** — get one from https://aistudio.google.com/app/apikey
   (Keep it secret — treat it like a password.)

To confirm Python is installed, open **PowerShell** and run:

```powershell
python --version
```

You should see something like `Python 3.11.5`.

---

## 7. Setup Instructions (Windows + VS Code, Step by Step)

### Step 1 — Open the project folder

Open VS Code, then **File → Open Folder**, and select the
`student-support-assistant` folder.

Open a terminal inside VS Code: **Terminal → New Terminal**. This opens
PowerShell inside the project folder — all commands below are run there.

### Step 2 — Create a virtual environment

A virtual environment keeps this project's Python packages separate from
everything else on your computer.

```powershell
python -m venv venv
```

### Step 3 — Activate the virtual environment

```powershell
venv\Scripts\Activate.ps1
```

If PowerShell blocks this with an error about "running scripts is
disabled", run this once (it only relaxes permissions for your user):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again. When activated, you'll see `(venv)` at the
start of your terminal prompt.

### Step 4 — Install required packages

```powershell
pip install -r backend/requirements.txt
```

This installs FastAPI, Uvicorn, the Gemini SDK, ChromaDB, pypdf, and
everything else needed. It may take a few minutes the first time.

### Step 5 — Create your `.env` file

Copy `.env.example` to a new file named exactly `.env` in the project
root folder. You can do this in PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code and replace `your_api_key_here` with your real
Gemini API key:

```
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Save the file. **Never share this file or upload it anywhere public.**

### Step 6 — Add your college documents

Put your PDF/TXT files (syllabus, regulations, notices, FAQs) inside:

```
backend/data/documents/
```

A sample document (`sample_college_regulations.txt`) is already there so
you can test right away. It is clearly labeled as **SAMPLE DATA** — feel
free to delete it once you add your real documents.

### Step 7 — Run document ingestion

This reads your documents, creates embeddings, and stores them in
ChromaDB. Run this from the project root (with `venv` activated):

```powershell
python -m backend.rag.ingest
```

You should see output like:

```
Found 1 file(s): sample_college_regulations.txt
Processing: sample_college_regulations.txt
  -> 3 chunk(s) created
Embedding and storing 3 chunk(s)...
[SUCCESS] Ingestion complete!
```

**Re-run this command every time you add, remove, or edit documents.**

### Step 8 — Start the backend server

```powershell
uvicorn backend.main:app --reload
```

You should see:

```
Uvicorn running on http://127.0.0.1:8000
```

Keep this terminal window open — it needs to keep running while you use
the assistant.

You can visit `http://127.0.0.1:8000` in a browser to see a health-check
JSON response confirming the server, API key, and knowledge base status.

### Step 9 — Open the frontend

The frontend is plain HTML/CSS/JS, so you can simply open it in your
browser. In VS Code's file explorer, right-click `frontend/index.html`
and choose **"Open with Live Server"** (if you have that extension), or
just double-click `frontend/index.html` in File Explorer to open it
directly in your browser.

> If you open `index.html` directly (via `file://`), the app will still
> work as long as the backend is running at `http://127.0.0.1:8000` —
> CORS is already enabled in the backend to allow this.

You should now see the **Student Support Assistant** chat interface.
Type a question and press **Send**.

---

## 8. Example Questions to Try

Using the included sample document:

- "What is the attendance requirement?"
- "Can I bring my phone into the exam hall?"
- "How many books can I borrow from the library?"
- "What are the college working hours?" *(uses the College Info tool)*
- "Find notices about holidays." *(uses the Notice Search tool)*
- "What is the hostel fee for next semester?" *(should say information not found)*

Try this memory example:

1. "My department is CSE."
2. "Who do I contact in my department?" (the assistant should understand
   "my department" means CSE from the previous message)

---

## 9. How RAG Works (In Simple Terms)

1. **Ingestion (offline, run manually):** Every PDF/TXT in
   `backend/data/documents/` is read, split into small overlapping text
   "chunks" (~1000 characters each), and each chunk is converted into an
   **embedding** — a list of numbers representing its meaning. Chunks and
   embeddings are stored in **ChromaDB**, a local vector database saved
   to the `chroma_db/` folder.
2. **Retrieval (happens per question):** When a student asks a question,
   the question itself is turned into an embedding, and ChromaDB finds
   the chunks whose embeddings are most similar (closest in meaning).
3. **Generation:** Those chunks are inserted into the prompt sent to
   Gemini, along with an instruction to answer **only** using that
   information — and to say "I could not find this information..." if
   the answer isn't there. This prevents hallucination.
4. **Sources:** Each retrieved chunk carries its filename and page
   number as metadata, which is shown back to the student.

---

## 10. How Memory Works

Each browser session gets a random `session_id` (stored in
`sessionStorage`, generated in `script.js`). Every message sent to
`/chat` includes this ID. The backend (`memory/memory_store.py`) keeps a
Python dictionary like:

```python
{
  "session-abc123": [
      {"role": "user", "content": "My department is CSE."},
      {"role": "assistant", "content": "Okay, noted!"},
  ]
}
```

This history is included in every request sent to Gemini, so it can
understand references like "my department" from earlier in the
conversation. Clicking **"Clear Chat"** calls `/reset`, which deletes
that session's history and starts a fresh session ID.

Note: this memory lives only in the server's RAM — restarting the
backend clears all conversations. That's expected for this beginner
version.

---

## 11. How Tools Work

Gemini's API supports **function calling**: we describe available tools
(name, description, expected inputs), and Gemini decides on its own
whether it needs to call one to answer the question.

- **`notice_search(keyword)`** — searches all ingested document chunks
  for a keyword and returns matching filenames/snippets. Used for
  requests like "find notices about exams."
- **`college_info(topic)`** — looks up structured data (working hours,
  department contacts, exam cell, etc.) from a Python dictionary in
  `tools/college_info.py`, clearly marked as **SAMPLE DATA**.

When Gemini requests a tool, the backend (`chat/assistant.py`) runs the
matching Python function, sends the result back to Gemini, and Gemini
uses it to write the final answer — all automatically, in one `/chat`
request.

---

## 12. Editing the Sample College Information

Open `backend/tools/college_info.py` and edit the `COLLEGE_INFO`
dictionary with your real college's working hours, department contacts,
etc. It's plain Python — just replace the sample text values, keeping
the same structure (keys like `"working_hours"`, `"departments"`, etc.).

---

## 13. Troubleshooting

| Problem | Likely Cause / Fix |
|---|---|
| `GEMINI_API_KEY` missing error in chat | You haven't created `.env`, or forgot to set the key. See Step 5. |
| "Gemini API key was rejected" | The key in `.env` is incorrect or expired — get a new one from Google AI Studio. |
| "Could not reach the backend" in the UI | The backend server isn't running, or crashed. Check the terminal running `uvicorn`. |
| Assistant always says "I could not find this information..." | You haven't run ingestion yet, or your documents don't mention that topic. Run `python -m backend.rag.ingest`. |
| Ingestion says "No PDF or TXT files found" | Add files to `backend/data/documents/` first. |
| PDF gives 0 chunks / no text extracted | The PDF might be a scanned image with no selectable text. This project does not include OCR; use a text-based PDF instead. |
| `venv\Scripts\Activate.ps1` blocked by PowerShell | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once, then retry. |
| `ModuleNotFoundError` for fastapi/google.genai/etc. | Make sure `(venv)` is shown in your terminal (virtual environment activated) and you ran `pip install -r backend/requirements.txt`. |
| CORS error in browser console | Make sure the backend is running and `API_BASE_URL` in `frontend/script.js` matches (`http://127.0.0.1:8000` by default). |
| Port 8000 already in use | Stop whatever else is using it, or run `uvicorn backend.main:app --reload --port 8001` and update `API_BASE_URL` in `script.js` to match. |
| Answers seem to ignore earlier messages | Make sure you're not clicking "Clear Chat" between questions, and that you're testing within the same browser tab (same session). |

---

## 14. Testing Checklist

Use this checklist to confirm everything works:

1. **Simple college question** — Ask "What is the attendance requirement?" → should get a grounded answer with a source.
2. **Question answered from a PDF** — Add a real PDF, re-ingest, ask a question only that PDF answers.
3. **Question where information is unavailable** — Ask something unrelated/not in your documents → should get the "I could not find this information..." message.
4. **Follow-up question using memory** — Say "My department is CSE," then ask "Who do I contact in my department?"
5. **Notice search tool** — Ask "Find notices about holidays."
6. **College information tool** — Ask "What are the college working hours?"
7. **Empty message** — Try sending a blank message → should show a friendly validation message, no crash.
8. **Invalid API key** — Temporarily break the key in `.env`, restart server, ask a question → should show a friendly error, not a crash.
9. **Reset conversation** — Click "Clear Chat," then ask a follow-up that relied on earlier context → assistant should no longer remember it.
10. **Source references** — Confirm that grounded answers show a "Sources:" section with filename (and page number for PDFs).

---

## 15. Future Improvements

- Persist conversation memory in a real database (e.g. SQLite or Redis) instead of an in-memory dictionary, so history survives server restarts.
- Add user authentication so each real student has their own private history.
- Add OCR support for scanned PDF documents.
- Add a document upload button directly in the frontend (instead of manually placing files in a folder).
- Add streaming responses so answers appear word-by-word.
- Add an admin page to edit `college_info.py` data through the UI instead of code.
- Add automated tests (e.g. with `pytest`) for the RAG, tools, and memory modules.

---

## 16. Security Notes

- The Gemini API key lives **only** in the backend's `.env` file and is
  never sent to the frontend or exposed in any API response.
- `.env` is listed in `.gitignore` — never commit it to version control.
- `chroma_db/` (your document embeddings) and `__pycache__/` are also
  git-ignored.

---

That's it — you now have a complete, working AI Student Support
Assistant demonstrating RAG, Tools, and Memory. Good luck with your
Naan Mudhalvan submission!
