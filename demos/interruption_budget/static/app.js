const decision = document.querySelector("#decision");
const why = document.querySelector("#why");
const preference = document.querySelector("#preference");
const quiet = document.querySelector("#quiet");
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

function render(inbox) {
  word(inbox.decision);
  preference.textContent = inbox.preference;
  why.textContent = inbox.note;
  quiet.setAttribute("aria-pressed", String(inbox.quiet));
  sheet.innerHTML = `<div class="bays">${inbox.columns.map((column) => `
    <section class="bay">
      <h2>${column.title}</h2>
      ${column.events.length ? column.events.map((event) => `
        <article class="strip${event.split ? " split" : ""}">
          <p>${event.text}</p>
          <p class="meta">${event.note}</p>
        </article>`).join("") : `<p class="empty">Nothing in this bay.</p>`}
    </section>`).join("")}</div>`;
}

async function show(isQuiet) {
  const response = await fetch(`/api/inbox?quiet=${isQuiet ? "1" : "0"}`);
  if (!response.ok) {
    word("Offline");
    why.textContent = "Quiet hours needs a yes or no.";
    return;
  }
  render(await response.json());
}

async function start() {
  quiet.addEventListener("click", () => show(quiet.getAttribute("aria-pressed") !== "true"));
  try {
    await show(false);
  } catch {
    word("Offline");
    why.textContent = "Start the local page with python3 demos/interruption_budget/interruption_budget.py serve";
  }
}

start();
