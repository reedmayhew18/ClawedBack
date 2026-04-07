// clawed-back chat UI

const $ = (sel) => document.querySelector(sel);
const TOKEN_KEY = "oc_token";

// --- Markdown rendering ---
// marked.js (MIT) + DOMPurify (Apache 2.0) loaded in index.html
const md = (() => {
    if (typeof marked === "undefined") return (s) => s;
    marked.setOptions({
        breaks: true,       // GFM line breaks
        gfm: true,          // GitHub Flavored Markdown
        headerIds: false,    // no auto IDs on headers
        mangle: false,       // don't mangle email addresses
    });
    return (text) => {
        const html = marked.parse(text);
        if (typeof DOMPurify !== "undefined") {
            return DOMPurify.sanitize(html, {
                ADD_ATTR: ["target"],
                ALLOW_DATA_ATTR: false,
            });
        }
        return html;
    };
})();

let token = localStorage.getItem(TOKEN_KEY);
let eventSource = null;
let mediaRecorder = null;
let audioChunks = [];
let pendingAttachments = [];
let renderedMsgIds = { user: new Set(), assistant: new Set() };
let pendingLocalMessages = new Set(); // content hashes of messages we sent locally

// --- Init ---

function init() {
    if (token) {
        showChat();
    } else {
        showLogin();
    }

    // Login
    $("#login-btn").addEventListener("click", login);
    $("#token-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter") login();
    });

    // Chat
    $("#send-btn").addEventListener("click", sendMessage);
    $("#message-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    $("#message-input").addEventListener("input", autoResize);
    $("#file-input").addEventListener("change", handleFileSelect);
    $("#voice-btn").addEventListener("click", toggleVoice);
    $("#stop-record-btn").addEventListener("click", stopRecording);
    $("#logout-btn").addEventListener("click", logout);
}

// --- Auth ---

async function login() {
    const input = $("#token-input");
    const err = $("#login-error");
    const t = input.value.trim();
    if (!t) return;

    try {
        const res = await fetch("/api/auth", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: t }),
        });
        if (res.ok) {
            token = t;
            localStorage.setItem(TOKEN_KEY, token);
            err.classList.add("hidden");
            showChat();
        } else {
            err.textContent = "Invalid token.";
            err.classList.remove("hidden");
        }
    } catch {
        err.textContent = "Connection failed.";
        err.classList.remove("hidden");
    }
}

function logout() {
    token = null;
    localStorage.removeItem(TOKEN_KEY);
    if (sseAbort) sseAbort.abort();
    showLogin();
}

// --- Screens ---

function showLogin() {
    $("#login-screen").classList.remove("hidden");
    $("#chat-screen").classList.add("hidden");
    $("#token-input").value = "";
    $("#token-input").focus();
}

function showChat() {
    $("#login-screen").classList.add("hidden");
    $("#chat-screen").classList.remove("hidden");
    $("#message-input").focus();
    loadHistory();
    connectSSE();
}

// --- SSE (fetch-based for secure auth via header) ---

let sseAbort = null;

function connectSSE() {
    if (sseAbort) sseAbort.abort();
    sseAbort = new AbortController();

    fetchSSE(sseAbort.signal);
}

async function fetchSSE(signal) {
    try {
        const res = await fetch("/api/events", {
            headers: { "Authorization": `Bearer ${token}` },
            signal,
        });

        if (!res.ok) {
            $("#status-indicator").className = "status offline";
            $("#status-indicator").title = "Disconnected";
            if (res.status === 401) { logout(); return; }
            setTimeout(() => fetchSSE(signal), 3000);
            return;
        }

        $("#status-indicator").className = "status online";
        $("#status-indicator").title = "Connected";

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop(); // keep incomplete line in buffer

            let currentEvent = "message";
            for (const line of lines) {
                if (line.startsWith("event:")) {
                    currentEvent = line.slice(6).trim();
                } else if (line.startsWith("data:")) {
                    const raw = line.slice(5).trim();
                    if (!raw) continue;
                    try {
                        const data = JSON.parse(raw);
                        if (currentEvent === "read_receipt") {
                            updateReadReceipts(data.read_up_to);
                        } else if (currentEvent === "user_message") {
                            if (!renderedMsgIds.user.has(data.id)) {
                                renderedMsgIds.user.add(data.id);
                                if (data.type === "voice") {
                                    // Voice messages rendered by uploadVoice() — never re-append
                                    stampLocalMessage(data.content, data.id);
                                } else if (pendingLocalMessages.has(data.content)) {
                                    pendingLocalMessages.delete(data.content);
                                    stampLocalMessage(data.content, data.id);
                                } else {
                                    appendMessage("user", data.content, data.timestamp, data.metadata, data.id);
                                }
                            }
                        } else {
                            if (!renderedMsgIds.assistant.has(data.id)) {
                                renderedMsgIds.assistant.add(data.id);
                                appendMessage("assistant", data.content, data.timestamp, data.metadata, data.id);
                            }
                        }
                    } catch {}
                    currentEvent = "message"; // reset after processing data
                }
            }
        }
    } catch (e) {
        if (e.name === "AbortError") return;
        $("#status-indicator").className = "status offline";
        $("#status-indicator").title = "Disconnected";
    }

    // Auto-reconnect after disconnect (unless aborted)
    if (!signal.aborted) {
        setTimeout(() => fetchSSE(signal), 3000);
    }
}

// --- Messages ---

async function loadHistory() {
    try {
        const res = await apiFetch("/api/history");
        const data = await res.json();
        const container = $("#messages");
        container.innerHTML = "";
        renderedMsgIds = { user: new Set(), assistant: new Set() };
        for (const msg of data.messages) {
            const meta = typeof msg.metadata === "string" ? JSON.parse(msg.metadata) : msg.metadata;
            if (msg.id) renderedMsgIds[msg.role].add(msg.id);
            appendMessage(msg.role, msg.content, msg.timestamp, meta, msg.id);
            // Mark read receipts for already-processed messages
            if (msg.role === "user" && msg.processed >= 1 && msg.id) {
                setTimeout(() => updateReadReceipts(msg.id), 0);
            }
        }
    } catch (e) {
        console.error("Failed to load history:", e);
    }
}

function appendMessage(role, content, timestamp, metadata, msgId) {
    const container = $("#messages");
    const div = document.createElement("div");
    div.className = `message ${role}`;
    if (role === "user" && msgId) div.dataset.msgId = msgId;

    // Render markdown for both user and assistant messages
    const body = document.createElement("div");
    body.className = "message-body";
    body.innerHTML = md(content);
    // Make links open in new tab
    body.querySelectorAll("a").forEach((a) => {
        a.target = "_blank";
        a.rel = "noopener noreferrer";
    });
    div.appendChild(body);

    // Timestamp + read receipt for user messages
    const meta = document.createElement("div");
    meta.className = "meta";
    const date = new Date(timestamp * 1000);
    let metaText = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    if (role === "user" && msgId) {
        const check = document.createElement("span");
        check.className = "read-receipt";
        check.textContent = " \u2713";
        check.style.display = "none";
        meta.textContent = metaText;
        meta.appendChild(check);
    } else {
        meta.textContent = metaText;
    }
    div.appendChild(meta);

    // Attachments
    if (metadata?.attachments?.length) {
        const att = document.createElement("div");
        att.className = "attachments-list";
        att.textContent = "\u{1F4CE} " + metadata.attachments.join(", ");
        div.appendChild(att);
    }

    // Voice indicator
    if (metadata?.audio_file) {
        const voice = document.createElement("div");
        voice.className = "attachments-list";
        voice.textContent = "\u{1F3A4} Voice message";
        div.appendChild(voice);
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function stampLocalMessage(content, dbId) {
    // Find the locally-appended user message (no data-msg-id yet) and give it the real DB ID
    const msgs = document.querySelectorAll(".message.user:not([data-msg-id])");
    for (const el of msgs) {
        // Match by content (first text node)
        const bodyEl = el.querySelector(".message-body");
        if (bodyEl && bodyEl.textContent.trim() === content.trim()) {
            el.dataset.msgId = dbId;
            // Add read receipt indicator if not already present
            const meta = el.querySelector(".meta");
            if (meta && !meta.querySelector(".read-receipt")) {
                const check = document.createElement("span");
                check.className = "read-receipt";
                check.textContent = " \u2713";
                check.style.display = "none";
                meta.appendChild(check);
            }
            break;
        }
    }
}

function updateReadReceipts(readUpTo) {
    document.querySelectorAll(".message.user[data-msg-id]").forEach((el) => {
        const id = parseInt(el.dataset.msgId, 10);
        if (id <= readUpTo) {
            const check = el.querySelector(".read-receipt");
            if (check) check.style.display = "inline";
        }
    });
}

async function sendMessage() {
    const input = $("#message-input");
    const text = input.value.trim();
    if (!text && pendingAttachments.length === 0) return;

    const attachments = pendingAttachments.map((a) => a.filename);
    pendingLocalMessages.add(text);
    appendMessage("user", text || "(file upload)", Date.now() / 1000, { attachments });

    input.value = "";
    autoResize();
    clearAttachments();

    try {
        await apiFetch("/api/message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: text, attachments }),
        });
    } catch (e) {
        appendMessage("assistant", `Error: ${e.message}`, Date.now() / 1000, {});
    }
}

// --- File upload ---

async function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    for (const file of files) {
        try {
            const form = new FormData();
            form.append("file", file);
            const res = await apiFetch("/api/upload", { method: "POST", body: form });
            const data = await res.json();
            pendingAttachments.push({ filename: data.filename, original: data.original_name });
            renderAttachments();
        } catch (err) {
            console.error("Upload failed:", err);
        }
    }
    e.target.value = "";
}

function renderAttachments() {
    const container = $("#attachments-preview");
    if (pendingAttachments.length === 0) {
        container.classList.add("hidden");
        container.innerHTML = "";
        return;
    }
    container.classList.remove("hidden");
    container.innerHTML = pendingAttachments
        .map((a, i) => `
            <div class="attachment-chip">
                <span>${a.original || a.filename}</span>
                <button onclick="removeAttachment(${i})">\u2715</button>
            </div>
        `).join("");
}

window.removeAttachment = function (idx) {
    pendingAttachments.splice(idx, 1);
    renderAttachments();
};

function clearAttachments() {
    pendingAttachments = [];
    renderAttachments();
}

// --- Voice recording ---

async function toggleVoice() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        stopRecording();
        return;
    }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
            stream.getTracks().forEach((t) => t.stop());
            const blob = new Blob(audioChunks, { type: "audio/webm" });
            await uploadVoice(blob);
        };

        mediaRecorder.start();
        $("#voice-btn").classList.add("recording");
        $("#recording-indicator").classList.remove("hidden");
    } catch (err) {
        console.error("Mic access denied:", err);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }
    $("#voice-btn").classList.remove("recording");
    $("#recording-indicator").classList.add("hidden");
}

async function uploadVoice(blob) {
    // Show "Transcribing..." placeholder immediately
    const container = $("#messages");
    const placeholder = document.createElement("div");
    placeholder.className = "message user";
    const pBody = document.createElement("div");
    pBody.className = "message-body";
    pBody.innerHTML = "<em>Transcribing\u2026</em>";
    placeholder.appendChild(pBody);
    const pMeta = document.createElement("div");
    pMeta.className = "meta";
    pMeta.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    placeholder.appendChild(pMeta);
    container.appendChild(placeholder);
    container.scrollTop = container.scrollHeight;

    const form = new FormData();
    form.append("file", blob, "recording.webm");
    try {
        const res = await apiFetch("/api/voice", { method: "POST", body: form });
        const data = await res.json();
        // Update placeholder in-place with transcribed text
        pBody.innerHTML = md(data.text);
        pBody.querySelectorAll("a").forEach((a) => {
            a.target = "_blank";
            a.rel = "noopener noreferrer";
        });
        const voiceTag = document.createElement("div");
        voiceTag.className = "attachments-list";
        voiceTag.textContent = "\u{1F3A4} Voice message";
        placeholder.appendChild(voiceTag);
        pendingLocalMessages.add(data.text);
    } catch (err) {
        placeholder.remove();
        appendMessage("assistant", `Voice error: ${err.message}`, Date.now() / 1000, {});
    }
}

// --- Helpers ---

function apiFetch(url, opts = {}) {
    opts.headers = opts.headers || {};
    if (token) opts.headers["Authorization"] = `Bearer ${token}`;
    return fetch(url, opts).then((res) => {
        if (res.status === 401) { logout(); throw new Error("Session expired"); }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res;
    });
}

function autoResize() {
    const el = $("#message-input");
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
}

// --- Drag and drop ---

document.addEventListener("dragover", (e) => e.preventDefault());
document.addEventListener("drop", async (e) => {
    e.preventDefault();
    if (!token) return;
    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
        const form = new FormData();
        form.append("file", file);
        try {
            const res = await apiFetch("/api/upload", { method: "POST", body: form });
            const data = await res.json();
            pendingAttachments.push({ filename: data.filename, original: data.original_name });
            renderAttachments();
        } catch (err) {
            console.error("Drop upload failed:", err);
        }
    }
});

// --- Boot ---
init();
