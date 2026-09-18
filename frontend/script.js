/* ---------------------------------------------------------
   Student Support Assistant - Frontend Logic
   Plain JavaScript (no frameworks).
--------------------------------------------------------- */

// IMPORTANT: This must match the address your FastAPI backend is
// running on. By default, "uvicorn backend.main:app --reload" runs on
// http://127.0.0.1:8000
const API_BASE_URL = "http://127.0.0.1:8000";

const chatArea = document.getElementById("chatArea");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const clearChatButton = document.getElementById("clearChatButton");
const loadingIndicator = document.getElementById("loadingIndicator");
const errorArea = document.getElementById("errorArea");
const sessionLabel = document.getElementById("sessionLabel");

// --- Session ID -----------------------------------------------------
// A simple random ID is generated per browser tab session and reused
// for every message, so the backend can remember the conversation.
function generateSessionId() {
  return "session-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
}

let sessionId = sessionStorage.getItem("ssa_session_id");
if (!sessionId) {
  sessionId = generateSessionId();
  sessionStorage.setItem("ssa_session_id", sessionId);
}
sessionLabel.textContent = "Session: " + sessionId.slice(0, 18) + "...";

// --- Helpers ----------------------------------------------------------

function showError(message) {
  errorArea.textContent = message;
  errorArea.classList.remove("hidden");
}

function clearError() {
  errorArea.textContent = "";
  errorArea.classList.add("hidden");
}

function setLoading(isLoading) {
  loadingIndicator.classList.toggle("hidden", !isLoading);
  sendButton.disabled = isLoading;
  messageInput.disabled = isLoading;
}

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

function addMessage(role, text, sources) {
  const wrapper = document.createElement("div");
  wrapper.className = "message " + (role === "user" ? "user-message" : "assistant-message");

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  if (sources && sources.length > 0) {
    const sourcesDiv = document.createElement("div");
    sourcesDiv.className = "sources";
    const title = document.createElement("strong");
    title.textContent = "Sources:";
    sourcesDiv.appendChild(title);

    sources.forEach((src) => {
      const line = document.createElement("div");
      const pageText = src.page ? `, Page ${src.page}` : "";
      line.textContent = `- ${src.filename}${pageText}`;
      sourcesDiv.appendChild(line);
    });

    bubble.appendChild(sourcesDiv);
  }

  chatArea.appendChild(wrapper);
  scrollToBottom();
}

// --- Sending a message --------------------------------------------------

async function sendMessage(message) {
  clearError();
  addMessage("user", message);
  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: message }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned status ${response.status}`);
    }

    const data = await response.json();
    addMessage("assistant", data.answer, data.sources);
  } catch (err) {
    console.error(err);
    showError(
      "Could not reach the backend. Make sure the FastAPI server is running " +
      `at ${API_BASE_URL} (see README.md for how to start it).`
    );
  } finally {
    setLoading(false);
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();

  if (!message) {
    showError("Please type a question before sending.");
    return;
  }

  messageInput.value = "";
  sendMessage(message);
});

// --- Clear chat -------------------------------------------------------

clearChatButton.addEventListener("click", async () => {
  clearError();
  try {
    await fetch(`${API_BASE_URL}/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
  } catch (err) {
    console.error(err);
    showError("Could not reach the backend to clear the conversation. It has been cleared locally only.");
  }

  // Reset UI regardless, and start a fresh session ID so memory is
  // truly separated from the previous conversation.
  chatArea.innerHTML = "";
  addMessage(
    "assistant",
    "Conversation cleared. Ask me anything about your college regulations, syllabus, or notices!"
  );

  sessionId = generateSessionId();
  sessionStorage.setItem("ssa_session_id", sessionId);
  sessionLabel.textContent = "Session: " + sessionId.slice(0, 18) + "...";
});
