const state = {
  docId: null,
  docs: [],
  report: null,
  sessionId: sessionStorage.getItem("docsense_session_id") || crypto.randomUUID(),
};

sessionStorage.setItem("docsense_session_id", state.sessionId);

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupUpload();
  setupChat();
  setupResearch();
  loadEvals();
});

function setupTabs() {
  $$(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      $$(".tab, .tab-panel").forEach((el) => el.classList.remove("active"));
      button.classList.add("active");
      $(`#${button.dataset.tab}`).classList.add("active");
      if (button.dataset.tab === "evals") loadEvals();
    });
  });
}

function setupUpload() {
  const dropzone = $("#dropzone");
  const input = $("#file-input");

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (event) => uploadFile(event.dataTransfer.files[0]));
  input.addEventListener("change", () => uploadFile(input.files[0]));
}

async function uploadFile(file) {
  if (!file) return;
  if (!file.name.match(/\.(pdf|txt)$/i)) {
    showToast("Only PDF and TXT files are supported.", true);
    return;
  }

  $("#selected-file").textContent = `✓ ${file.name}`;
  $("#selected-file").classList.remove("hidden");
  setProgress("Chunking...", 20);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/ingest", { method: "POST", body: formData });
    const payload = await parseJson(response);
    state.docId = payload.doc_id;
    setProgress("Embedding...", 55);
    await pollIngestStatus(payload.doc_id, file.name);
  } catch (error) {
    setProgress("Failed", 100);
    showToast(error.message, true);
  }
}

async function pollIngestStatus(docId, filename) {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    const response = await fetch(`/api/ingest/status/${docId}`);
    const payload = await parseJson(response);
    if (payload.status === "complete") {
      setProgress("Indexed ✓", 100);
      state.docs.push({ filename, chunk_count: payload.chunk_count, doc_id: docId });
      renderDocs();
      clearEmptyChat();
      showToast("Document indexed.");
      return;
    }
    if (payload.status === "failed") throw new Error("Document indexing failed.");
    await sleep(1500);
  }
  throw new Error("Indexing timed out.");
}

function setProgress(label, width) {
  $("#progress-wrap").classList.remove("hidden");
  $("#progress-label").textContent = label;
  $("#progress-bar").style.width = `${width}%`;
}

function renderDocs() {
  const list = $("#docs-list");
  list.classList.remove("empty");
  list.innerHTML = state.docs
    .map((doc) => `<div class="doc-item"><strong>${escapeHtml(doc.filename)}</strong><br><small>${doc.chunk_count} chunks</small></div>`)
    .join("");
}

function setupChat() {
  const form = $("#chat-form");
  const input = $("#question-input");

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) return;
    if (!state.docId) {
      showToast("Upload and index a document first.", true);
      return;
    }

    clearEmptyChat();
    addMessage("user", question);
    input.value = "";
    const typing = addTyping();

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, doc_id: state.docId, session_id: state.sessionId }),
      });
      const payload = await parseJson(response);
      typing.remove();
      addMessage("assistant", payload.answer, payload.sources);
    } catch (error) {
      typing.remove();
      showToast(error.message, true);
    }
  });
}

function clearEmptyChat() {
  const empty = $(".empty-state");
  if (empty) empty.remove();
}

function addMessage(role, content, sources = []) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.innerHTML = `<div>${escapeHtml(content).replace(/\n/g, "<br>")}</div>`;

  if (sources.length) {
    const details = document.createElement("details");
    details.className = "sources";
    details.innerHTML = `<summary>Sources</summary>${sources.map(renderSource).join("")}`;
    message.appendChild(details);
  }

  $("#chat-messages").appendChild(message);
  message.scrollIntoView({ behavior: "smooth", block: "end" });
}

function renderSource(source) {
  const pct = Math.max(4, Math.min(100, source.score * 100));
  return `
    <div class="source-card">
      <strong>${escapeHtml(source.filename)}${source.page ? ` · page ${source.page}` : ""}</strong>
      <div class="score-track"><div class="score-bar" style="width:${pct}%"></div></div>
      <p>${escapeHtml(source.text.slice(0, 320))}</p>
    </div>
  `;
}

function addTyping() {
  const node = document.createElement("div");
  node.className = "message assistant typing";
  node.innerHTML = "<span></span><span></span><span></span>";
  $("#chat-messages").appendChild(node);
  return node;
}

function setupResearch() {
  $("#research-button").addEventListener("click", startResearch);
  $("#download-report").addEventListener("click", downloadReport);
}

function startResearch() {
  const topic = $("#topic-input").value.trim();
  if (!topic) {
    showToast("Enter a research topic.", true);
    return;
  }

  $("#agent-log").innerHTML = "";
  $("#report").classList.add("hidden");
  $("#download-report").classList.add("hidden");
  $("#tool-count").textContent = "0";
  $("#time-taken").textContent = "0s";

  const stream = new EventSource(`/api/agent/research/stream?topic=${encodeURIComponent(topic)}`);
  stream.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "tool_call") {
      addLogLine(payload);
      $("#tool-count").textContent = String(Number($("#tool-count").textContent) + 1);
    }
    if (payload.type === "complete") {
      stream.close();
      state.report = payload.report;
      $("#tool-count").textContent = payload.tool_calls;
      $("#time-taken").textContent = `${payload.time_taken}s`;
      renderReport(payload.report);
    }
  };
  stream.onerror = () => {
    stream.close();
    showToast("Research stream failed.", true);
  };
}

function addLogLine(payload) {
  const icons = { web_search: "🔍", fetch_page: "📄", save_section: "📝" };
  const input = payload.input.query || payload.input.url || payload.input.title || "";
  const line = document.createElement("div");
  line.className = "log-line";
  line.textContent = `${icons[payload.tool] || "•"} [${payload.tool}] "${input}" · ${new Date(payload.timestamp).toLocaleTimeString()}`;
  $("#agent-log").appendChild(line);
}

function renderReport(report) {
  $("#report").innerHTML = `
    <h2>Overview</h2><p>${escapeHtml(report.overview || "No overview saved.")}</p>
    <h2>Key Findings</h2>${(report.findings || []).map((item) => `<h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.content)}</p>`).join("")}
    <h2>Conclusion</h2><p>${escapeHtml(report.conclusion || "No conclusion saved.")}</p>
    <h2>Sources</h2><ul>${(report.sources || []).map((source) => `<li>${escapeHtml(source)}</li>`).join("")}</ul>
  `;
  $("#report").classList.remove("hidden");
  $("#download-report").classList.remove("hidden");
}

function downloadReport() {
  if (!state.report) return;
  const markdown = [
    "# Research Report",
    "## Overview",
    state.report.overview || "",
    "## Key Findings",
    ...(state.report.findings || []).map((item) => `### ${item.title}\n${item.content}`),
    "## Conclusion",
    state.report.conclusion || "",
    "## Sources",
    ...(state.report.sources || []).map((source) => `- ${source}`),
  ].join("\n\n");
  const blob = new Blob([markdown], { type: "text/markdown" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "docsense-research-report.md";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function loadEvals() {
  try {
    const response = await fetch("/api/evals");
    const payload = await parseJson(response);
    $("#stat-total").textContent = payload.total_queries;
    $("#stat-avg").textContent = Number(payload.avg_sources).toFixed(1);
    $("#stat-positive").textContent = `${payload.positive_feedback_pct}%`;
    renderBars(payload.queries_per_day);
    renderEvalRows(payload.recent);
  } catch (error) {
    showToast(error.message, true);
  }
}

function renderBars(items) {
  const max = Math.max(1, ...items.map((item) => item.count));
  $("#bar-chart").innerHTML = items
    .map((item) => `<div class="bar"><div class="bar-fill" style="height:${(item.count / max) * 140}px"></div><small>${item.date}</small></div>`)
    .join("");
}

function renderEvalRows(rows) {
  $("#eval-table").innerHTML = rows
    .map(
      (row) => `
      <tr>
        <td>${escapeHtml(row.question)}</td>
        <td>${escapeHtml(row.answer_preview)}</td>
        <td>${row.sources_count}</td>
        <td>
          <div class="feedback-buttons">
            <button data-feedback="positive" data-id="${row.id}">👍</button>
            <button data-feedback="negative" data-id="${row.id}">👎</button>
          </div>
        </td>
        <td>${new Date(row.timestamp).toLocaleString()}</td>
      </tr>`
    )
    .join("");

  $$(".feedback-buttons button").forEach((button) => {
    button.addEventListener("click", async () => {
      await fetch(`/api/evals/${button.dataset.id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: button.dataset.feedback }),
      });
      loadEvals();
    });
  });
}

async function parseJson(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Request failed");
  return payload;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.style.borderColor = isError ? "var(--danger)" : "var(--border)";
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 3200);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
