const decision = document.querySelector("#decision");
const why = document.querySelector("#why");
const scenarios = document.querySelector("#scenarios");
const sheet = document.querySelector("#sheet");
const lock = document.querySelector("#lock");
const lockNote = document.querySelector("#lock-note");
const preview = document.querySelector("#preview");
const previewSheet = document.querySelector("#preview-sheet");

let board = null;
let lastWord = "";

function word(next) {
  if (next !== lastWord) {
    decision.animate(
      [{ filter: "blur(3px)" }, { filter: "blur(0px)" }],
      { duration: 200, easing: "cubic-bezier(0.16, 1, 0.3, 1)" },
    );
  }
  lastWord = next;
  decision.textContent = next;
}

function picks() {
  return [...sheet.querySelectorAll("select")].map((select) => ({
    header: select.dataset.header,
    target_id: select.value || null,
  }));
}

function fieldName(id) {
  if (!id) return "unmapped";
  return board.targets.find((target) => target.id === id)?.label || id;
}

function selectedTarget(column) {
  if (board.engine === "live_jev" && column.jev?.status === "suggested") return column.jev.target || "";
  if (board.engine === "live_jev" || board.engine === "unavailable") return "";
  return column.label || "";
}

function jevName(column) {
  if (!column.jev) return "No API key";
  if (column.jev.status === "unavailable") return "Unavailable";
  if (column.jev.status === "review") return `Review ${Number(column.jev.confidence).toFixed(2)}`;
  return `${fieldName(column.jev.target)} ${Number(column.jev.confidence).toFixed(2)}`;
}

function renderBoard() {
  const head = board.targets.map((target) => `<option value="${target.id}">${target.label}</option>`).join("");
  const rows = board.columns.map((column) => {
    const split = column.baseline !== column.label;
    const selected = selectedTarget(column);
    return `<tr class="${split ? "split" : ""}">
      <td data-label="Header">${column.header}</td>
      <td data-label="Samples" class="samples">${column.samples.join(", ")}</td>
      <td data-label="Baseline">${fieldName(column.baseline)}</td>
      <td data-label="Jev">${jevName(column)}</td>
      <td data-label="Scenario label" class="${split ? "mark" : ""}">${fieldName(column.label)}</td>
      <td data-label="Pick">
        <select data-header="${column.header}" aria-label="Pick for ${column.header}">
          <option value="" ${selected === "" ? "selected" : ""}>Unmapped</option>
          ${head.replace(`value="${selected}"`, `value="${selected}" selected`)}
        </select>
      </td>
    </tr>`;
  }).join("");
  sheet.innerHTML = `<table>
    <thead><tr><th>Header</th><th>Samples</th><th>Baseline</th><th>Jev</th><th>Scenario label</th><th>Pick</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
  sheet.querySelectorAll("select").forEach((select) => select.addEventListener("change", () => { preview.hidden = true; refresh(); }));
}

async function refresh() {
  const response = await fetch("/api/preview", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ scenario_id: board.id, choices: picks() }),
  });
  const body = await response.json();
  word(body.decision || "Offline");
  why.textContent = body.conflicts?.length
    ? `Conflict on ${body.conflicts.map((id) => fieldName(id)).join(", ")}. Two columns cannot lock the same field.`
    : board.note;
  lock.disabled = body.decision === "CONFLICT";
  lock.dataset.preview = JSON.stringify(body.preview || []);
}

function renderPreview(rows) {
  preview.hidden = false;
  previewSheet.innerHTML = `<table>
    <thead><tr><th>Header</th><th>Locked field</th><th>Samples</th></tr></thead>
    <tbody>${rows.map((row) => `<tr><td data-label="Header">${row.header}</td><td data-label="Locked field">${fieldName(row.target === "unmapped" ? null : row.target)}</td><td data-label="Samples" class="samples">${row.samples.join(", ")}</td></tr>`).join("")}</tbody>
  </table>`;
  lockNote.textContent = "Mapping locked on this page. Nothing was imported.";
}

async function show(id) {
  const response = await fetch(`/api/board?id=${encodeURIComponent(id)}`);
  if (!response.ok) {
    word("Offline");
    why.textContent = "That sheet is not in this fixture.";
    return;
  }
  board = await response.json();
  preview.hidden = true;
  lockNote.textContent = "";
  [...scenarios.children].forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.id === id)));
  renderBoard();
  await refresh();
}

async function start() {
  try {
    const response = await fetch("/api/scenarios");
    const body = await response.json();
    scenarios.innerHTML = body.scenarios.map((scenario) =>
      `<button type="button" data-id="${scenario.id}" aria-pressed="false">${scenario.title}</button>`).join("");
    scenarios.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (button) show(button.dataset.id);
    });
    lock.addEventListener("click", () => renderPreview(JSON.parse(lock.dataset.preview || "[]")));
    await show(body.scenarios[0].id);
  } catch {
    word("Offline");
    why.textContent = "Start the local page with python3 demos/field_matchmaker/field_matchmaker.py serve";
  }
}

start();
