const decision = document.querySelector("#decision");
const why = document.querySelector("#why");
const scenarios = document.querySelector("#scenarios");
const sheet = document.querySelector("#sheet");
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

function reading(verdict) {
  return verdict.replaceAll("_", " ");
}

function jevCopy(board) {
  if (board.engine === "live_jev" && board.jev?.status === "suggested") {
    return `Jev says ${reading(board.jev.verdict)} (${Number(board.jev.confidence).toFixed(2)}). Baseline says ${reading(board.baseline.verdict)}.`;
  }
  if (board.engine === "live_jev") {
    return `Jev confidence is ${Number(board.jev.confidence).toFixed(2)}, below 0.80, so this stays in review.`;
  }
  return board.note;
}

function jevSection(board) {
  if (!board.jev) {
    const title = board.engine === "unavailable" ? "Unavailable" : "No API key";
    return `<section><h2>Jev</h2><p class="verdict">${title}</p><p class="copy">${board.note}</p></section>`;
  }
  const verdict = board.jev.verdict ? reading(board.jev.verdict) : "Review";
  return `<section><h2>Jev</h2><p class="verdict">${verdict}</p><p class="copy">${jevCopy(board)}</p></section>`;
}

function render(board) {
  word(board.decision);
  why.textContent = board.engine === "offline_baseline" && board.split
    ? `${board.label.reason} Baseline still says ${reading(board.baseline.verdict)}.`
    : board.engine === "offline_baseline"
      ? board.label.reason
      : jevCopy(board);
  sheet.innerHTML = `<div class="pair">
    <section>
      <h2>Claim</h2>
      <p class="copy">${board.claim}</p>
      <h2>Evidence</h2>
      <p class="copy">${board.evidence}</p>
    </section>
    <section class="${board.split ? "cell split" : ""}">
      <h2>Baseline</h2>
      <p class="verdict">${reading(board.baseline.verdict)}</p>
      <p class="copy">${board.baseline.reason}</p>
    </section>
    ${jevSection(board)}
    <section>
      <h2>Scenario label</h2>
      <p class="verdict">${reading(board.label.verdict)}</p>
      <p class="copy">${board.label.reason}</p>
    </section>
  </div>`;
}

async function show(id) {
  const response = await fetch(`/api/board?id=${encodeURIComponent(id)}`);
  if (!response.ok) {
    word("Offline");
    why.textContent = "That claim is not in this fixture.";
    return;
  }
  [...scenarios.children].forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.id === id)));
  render(await response.json());
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
    await show(body.scenarios[0].id);
  } catch {
    word("Offline");
    why.textContent = "Start the local page with python3 demos/claim_check/claim_check.py serve";
  }
}

start();
