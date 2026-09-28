const decision = document.querySelector("#decision");
const why = document.querySelector("#why");
const scenarios = document.querySelector("#scenarios");
const sheet = document.querySelector("#sheet");
const form = document.querySelector("#check-form");
const claim = document.querySelector("#claim");
const evidence = document.querySelector("#evidence");
const run = document.querySelector("#run");
const keyStatus = document.querySelector("#key-status");
let revision = 0;

function reading(verdict) { return verdict.replaceAll("_", " "); }

function reset() {
  revision += 1;
  run.disabled = false;
  form.setAttribute("aria-busy", "false");
  decision.textContent = "Ready";
  why.textContent = "Run the check to compare your claim with the evidence.";
  sheet.replaceChildren();
}

function section(title, verdict, copy) {
  const element = document.createElement("section");
  const heading = document.createElement("h2");
  heading.textContent = title;
  element.append(heading);
  for (const [className, text] of [["verdict", verdict], ["copy", copy]]) {
    const p = document.createElement("p");
    p.className = className;
    p.textContent = text;
    element.append(p);
  }
  return element;
}

function render(board) {
  decision.textContent = board.decision;
  why.textContent = board.note;
  const pair = document.createElement("div");
  pair.className = "pair";
  pair.append(section("Keyword baseline", reading(board.baseline.verdict), board.baseline.reason));
  const verdict = board.jev?.verdict ? reading(board.jev.verdict) : board.engine === "live_jev" ? "Review" : board.engine === "unavailable" ? "Unavailable" : "No API key";
  pair.append(section("Jev", verdict, board.jev ? `Live result · confidence ${Number(board.jev.confidence).toFixed(2)} · ${board.jev.model}` : board.note));
  sheet.replaceChildren(pair);
}

form.addEventListener("input", () => {
  reset();
  [...scenarios.children].forEach(button => button.setAttribute("aria-pressed", "false"));
});
form.addEventListener("submit", async event => {
  event.preventDefault();
  const current = ++revision;
  run.disabled = true;
  form.setAttribute("aria-busy", "true");
  decision.textContent = "Checking…";
  why.textContent = "Waiting for the server. Jev requests can take up to 30 seconds.";
  sheet.replaceChildren();
  try {
    const response = await fetch("/api/check", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim: claim.value, evidence: evidence.value }),
    });
    const board = await response.json();
    if (current !== revision) return;
    if (!response.ok) throw new Error(board.error || "The check failed. Try again.");
    render(board);
  } catch (error) {
    if (current !== revision) return;
    decision.textContent = "Unable to check";
    why.textContent = error.message || "The local server is unavailable. Try again.";
  } finally {
    if (current === revision) {
      run.disabled = false;
      form.setAttribute("aria-busy", "false");
    }
  }
});

async function start() {
  const initialRevision = revision;
  try {
    const response = await fetch("/api/scenarios", { cache: "no-store" });
    if (!response.ok) throw new Error("Unable to load examples.");
    const body = await response.json();
    keyStatus.textContent = body.api_key_configured
      ? "TYPESAFE_API_KEY detected in this server. Jev is ready to try."
      : "No TYPESAFE_API_KEY in this server process. Checks use the keyword baseline.";
    for (const scenario of body.scenarios) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = scenario.title;
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => {
        claim.value = scenario.claim;
        evidence.value = scenario.evidence;
        reset();
        [...scenarios.children].forEach(item => item.setAttribute("aria-pressed", String(item === button)));
      });
      scenarios.append(button);
    }
    if (revision === initialRevision && !claim.value && !evidence.value) scenarios.firstElementChild?.click();
  } catch {
    keyStatus.textContent = "Could not check the server's API key status.";
    if (revision === initialRevision) why.textContent = "Examples could not load. Enter your own claim and evidence, then run the check.";
  }
}
start();
