
function appendInspection(container, inspection) {
  const details = document.createElement("details");
  details.className = "jev-inspection";
  const summary = document.createElement("summary");
  summary.textContent = "Inspect Jev request and response";
  const note = document.createElement("p");
  note.textContent = inspection?.note || "No Jev response is available for this result. Baselines, fixtures and code rules are not Jev thinking.";
  details.append(summary, note);
  if (inspection) {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify({ request: inspection.request, response: inspection.response }, null, 2);
    details.append(pre);
  }
  container.append(details);
}
const decision = document.querySelector("#decision");
const status = document.querySelector("#status");
const why = document.querySelector("#why");
const quiet = document.querySelector("#quiet");
const sheet = document.querySelector("#sheet");
const form = document.querySelector("#event-form");
const eventText = document.querySelector("#event-text");
const pageFlag = document.querySelector("#page");
const sort = document.querySelector("#sort");
const sample = document.querySelector("#sample");
let active = { custom: false };
let isQuiet = false;
let requestId = 0;

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function render(inbox) {
  decision.textContent = inbox.custom && inbox.engine === "offline_baseline" ? "Baseline" : inbox.decision;
  status.textContent = inbox.engine === "live_jev" ? "Live Jev result" :
    inbox.engine === "unavailable" ? "Jev unavailable" :
      inbox.engine === "code_rule" ? "Code rule result" : "Offline baseline · add TYPESAFE_API_KEY for Jev";
  why.textContent = inbox.note;
  quiet.setAttribute("aria-pressed", String(inbox.quiet));
  sheet.innerHTML = `<div class="bays">${inbox.columns.map((column) => `
    <section class="bay">
      <h2>${escapeHTML(column.title)}</h2>
      ${column.events.length ? column.events.map((event) => `
        <article class="strip${event.split ? " split" : ""}">
          <p>${escapeHTML(event.text)}</p>
          <p class="meta">${escapeHTML(event.note)}</p>
        </article>`).join("") : `<p class="empty">Nothing in this bay.</p>`}
    </section>`).join("")}</div>`;
  appendInspection(sheet, inbox.inspection);
}

async function show() {
  const current = ++requestId;
  decision.textContent = "Sorting";
  status.textContent = "Checking current input…";
  why.textContent = "";
  sheet.replaceChildren();
  sort.disabled = true;
  sample.disabled = true;
  quiet.setAttribute("aria-pressed", String(isQuiet));
  try {
    const response = active.custom
      ? await fetch("/api/sort", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: active.text, page: active.page, quiet: isQuiet }),
      })
      : await fetch(`/api/inbox?quiet=${isQuiet ? "1" : "0"}`);
    if (!response.ok) throw new Error("request failed");
    const inbox = await response.json();
    if (current === requestId) render(inbox);
  } catch {
    if (current === requestId) {
      decision.textContent = "Error";
      status.textContent = "Could not load the result. Try again.";
    }
  } finally {
    if (current === requestId) {
      sort.disabled = false;
      sample.disabled = false;
    }
  }
}

form.addEventListener("input", () => {
  active = { custom: true, text: eventText.value.trim(), page: pageFlag.checked };
  requestId++;
  sheet.replaceChildren();
  sort.disabled = false;
  sample.disabled = false;
  decision.textContent = "Ready";
  status.textContent = "Event edited. Sort it to see a current result.";
  why.textContent = "";
});
form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  active = { custom: true, text: eventText.value.trim(), page: pageFlag.checked };
  show();
});
sample.addEventListener("click", () => {
  active = { custom: false };
  show();
});
quiet.addEventListener("click", () => {
  isQuiet = !isQuiet;
  show();
});
show();
