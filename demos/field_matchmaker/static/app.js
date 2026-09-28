const decision = document.querySelector("#decision");
const why = document.querySelector("#why");
const scenarios = document.querySelector("#scenarios");
const sheet = document.querySelector("#sheet");
const lock = document.querySelector("#lock");
const lockNote = document.querySelector("#lock-note");
const preview = document.querySelector("#preview");
const previewSheet = document.querySelector("#preview-sheet");
const input = document.querySelector("#csv-input");
const suggest = document.querySelector("#suggest");
const engine = document.querySelector("#engine");
let board = null;
let source = null;
let fixture = null;
let version = 0;
let validated = null;

function invalidate() {
  version += 1;
  validated = null;
  lock.disabled = true;
  preview.hidden = true;
  lockNote.textContent = "";
  return version;
}

function clearBoard() {
  invalidate();
  board = null;
  sheet.replaceChildren();
  engine.textContent = "";
  suggest.disabled = false;
}

async function request(url, body) {
  const response = await fetch(url, body ? {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  } : undefined);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed. Try again.");
  return result;
}

function fieldName(id) {
  return board.targets.find((target) => target.id === id)?.label || "Unmapped";
}

function table(container, headings) {
  container.replaceChildren();
  const table = document.createElement("table");
  const row = table.createTHead().insertRow();
  headings.forEach((heading) => {
    const th = document.createElement("th");
    th.textContent = heading;
    th.scope = "col";
    row.append(th);
  });
  container.append(table);
  return table.createTBody();
}

function cell(row, label, text) {
  const td = row.insertCell();
  td.dataset.label = label;
  td.textContent = text;
  return td;
}

function picks() {
  return [...sheet.querySelectorAll("select")].map((select) => ({
    header: select.dataset.header, target_id: select.value || null,
  }));
}

function renderBoard() {
  const headings = ["Header", "Samples", "Alias baseline", "Jev"];
  if (board.has_labels) headings.push("Fixture label");
  headings.push("Pick");
  const tbody = table(sheet, headings);
  board.columns.forEach((column) => {
    const row = tbody.insertRow();
    cell(row, "Header", column.header);
    cell(row, "Samples", column.samples.join(", "));
    cell(row, "Alias baseline", fieldName(column.baseline));
    const reading = column.jev;
    cell(row, "Jev", !reading ? "Not run" : reading.status === "unavailable" ? "Unavailable"
      : reading.status === "review" ? `Needs review (${reading.confidence.toFixed(2)})`
        : `${fieldName(reading.target)} (${reading.confidence.toFixed(2)})`);
    if (board.has_labels) cell(row, "Fixture label", fieldName(column.label));
    const select = document.createElement("select");
    select.dataset.header = column.header;
    select.setAttribute("aria-label", `Pick for ${column.header}`);
    select.add(new Option("Unmapped", ""));
    board.targets.forEach((target) => select.add(new Option(target.label, target.id)));
    select.value = board.engine === "offline_baseline" ? column.baseline || ""
      : reading?.status === "suggested" ? reading.target || "" : "";
    select.addEventListener("change", refresh);
    cell(row, "Pick", "").append(select);
  });
}

async function refresh() {
  const current = invalidate();
  decision.textContent = "Checking";
  why.textContent = "Validating the selected fields…";
  try {
    const body = await request("/api/preview", { ...source, choices: picks() });
    if (current !== version) return;
    decision.textContent = body.decision;
    why.textContent = body.conflicts.length
      ? `Conflict on ${body.conflicts.map(fieldName).join(", ")}. Choose a different field or leave a column unmapped.`
      : "Each field has at most one column. Review the picks, then lock this preview.";
    if (["CLEAR", "SPLIT"].includes(body.decision) && Array.isArray(body.preview)) {
      validated = body.preview;
      lock.disabled = false;
    }
  } catch (error) {
    if (current !== version) return;
    decision.textContent = "Error";
    why.textContent = `Mapping could not be validated. ${error.message}`;
  }
}

async function show(id) {
  clearBoard();
  fixture = null;
  const current = version;
  decision.textContent = "Loading";
  why.textContent = "Loading example CSV…";
  try {
    const body = await request(`/api/fixture?id=${encodeURIComponent(id)}`);
    if (current !== version) return;
    input.value = body.csv;
    fixture = { id, csv: body.csv };
    [...scenarios.children].forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.id === id)));
    decision.textContent = "Ready";
    why.textContent = "Edit this example or paste your CSV, then select Suggest mapping.";
  } catch (error) {
    if (current !== version) return;
    decision.textContent = "Error";
    why.textContent = error.message;
  }
}

input.addEventListener("input", () => {
  clearBoard();
  fixture = null;
  [...scenarios.children].forEach((button) => button.setAttribute("aria-pressed", "false"));
  decision.textContent = "Ready";
  why.textContent = "CSV changed. Select Suggest mapping to test it.";
});

document.querySelector("#csv-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearBoard();
  const current = version;
  source = fixture && input.value === fixture.csv ? { scenario_id: fixture.id } : { csv: input.value };
  suggest.disabled = true;
  decision.textContent = "Working";
  why.textContent = "Requesting suggestions…";
  engine.textContent = "Pending";
  try {
    const body = await request("/api/board", source);
    if (current !== version) return;
    board = body;
    suggest.disabled = false;
    engine.textContent = `${board.engine === "live_jev" ? "Live Jev" : board.engine === "offline_baseline" ? "Offline baseline" : "Jev unavailable"}. ${board.note}`;
    renderBoard();
    await refresh();
  } catch (error) {
    if (current !== version) return;
    suggest.disabled = false;
    decision.textContent = "Error";
    engine.textContent = "No result";
    why.textContent = error.message;
  }
});

lock.addEventListener("click", () => {
  if (!validated || lock.disabled) return;
  const tbody = table(previewSheet, ["Header", "Locked field", "Samples"]);
  validated.forEach((item) => {
    const row = tbody.insertRow();
    cell(row, "Header", item.header);
    cell(row, "Locked field", fieldName(item.target));
    cell(row, "Samples", item.samples.join(", "));
  });
  preview.hidden = false;
  lockNote.textContent = "Mapping locked on this page. Nothing was imported.";
});

async function start() {
  try {
    const body = await request("/api/scenarios");
    body.scenarios.forEach((scenario) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.id = scenario.id;
      button.textContent = scenario.title;
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => show(scenario.id));
      scenarios.append(button);
    });
    await show(body.scenarios[0].id);
  } catch (error) {
    decision.textContent = "Error";
    why.textContent = `Could not load examples. ${error.message}`;
  }
}
start();
