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

function render(board) {
  word(board.decision);
  why.textContent = board.split
    ? `${board.label.reason} Baseline still says ${board.baseline.verdict.replaceAll("_", " ")}.`
    : board.label.reason;
  sheet.innerHTML = `<div class="pair">
    <section>
      <h2>Claim</h2>
      <p class="copy">${board.claim}</p>
      <h2>Evidence</h2>
      <p class="copy">${board.evidence}</p>
    </section>
    <section class="${board.split ? "cell split" : ""}">
      <h2>Baseline</h2>
      <p class="verdict">${board.baseline.verdict.replaceAll("_", " ")}</p>
      <p class="copy">${board.baseline.reason}</p>
    </section>
    <section>
      <h2>Scenario label</h2>
      <p class="verdict">${board.label.verdict.replaceAll("_", " ")}</p>
      <p class="copy">${board.note}</p>
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
