(() => {
  const ENDPOINT = "POST https://api.typesafe.ai/v1/systemone";
  const demosUrl = document.body.dataset.demos || "/api/demos";
  const stage = document.getElementById("stage");
  const statusEl = document.getElementById("status");

  const state = { demo: "", help: "", demos: [] };
  let booted = false;
  let lastDemo = "";

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function commandHtml(command) {
    return escapeHtml(command).replaceAll("/", "/<wbr>");
  }

  function jsonHtml(value, path, indent) {
    const pad = "  ".repeat(indent);
    const inner = "  ".repeat(indent + 1);
    if (value === null) return '<span class="nil">null</span>';
    if (typeof value === "string") return `<span class="str">&quot;${escapeHtml(value)}&quot;</span>`;
    if (typeof value === "number" || typeof value === "boolean") return `<span class="num">${value}</span>`;
    if (Array.isArray(value)) {
      if (!value.length) return "[]";
      const rows = value.map((item, index) => `${inner}${jsonHtml(item, `${path}.${index}`, indent + 1)}`);
      return `[\n${rows.join(",\n")}\n${pad}]`;
    }
    const keys = Object.keys(value);
    if (!keys.length) return "{}";
    const rows = keys.map((key) => {
      const child = path ? `${path}.${key}` : key;
      return `${inner}<span class="line" data-path="${escapeHtml(child)}"><span class="key">&quot;${escapeHtml(key)}&quot;</span>: ${jsonHtml(value[key], child, indent + 1)}</span>`;
    });
    return `{\n${rows.join(",\n")}\n${pad}}`;
  }

  function currentDemo() {
    return state.demos.find((demo) => demo.id === state.demo) || state.demos[0];
  }

  function readUrl() {
    const params = new URLSearchParams(location.search);
    const demo = params.get("demo") || (state.demos[0] && state.demos[0].id) || "";
    state.demo = state.demos.some((item) => item.id === demo) ? demo : state.demos[0].id;
  }

  function writeUrl() {
    const url = new URL(location.href);
    url.searchParams.set("demo", state.demo);
    history.replaceState(null, "", url);
  }

  function rawBlock(caption, value, path) {
    return `<div class="pane"><span class="caption">${escapeHtml(caption)}</span><pre tabindex="0">${jsonHtml(value, path, 0)}</pre></div>`;
  }

  function helperButtons(demo) {
    return `<div class="helpers">${demo.helpers.map((helper) => `
      <button type="button" class="helper" data-help="${escapeHtml(helper.path)}" aria-pressed="${state.help === helper.path}">
        <span class="path">${escapeHtml(helper.path)}</span>
        ${escapeHtml(helper.text)}
      </button>`).join("")}</div>`;
  }

  function runCell(demo) {
    const link = demo.open
      ? `<a href="${escapeHtml(demo.open)}">${escapeHtml(demo.open.replace("http://", ""))}</a>`
      : "No browser page. This demo is a command.";
    const note = demo.port_note ? `<p>${escapeHtml(demo.port_note)}</p>` : "";
    return `<p class="cmd">${commandHtml(demo.command)}</p><p>${link}</p>${note}<p>Registry id ${escapeHtml(demo.id)}</p>`;
  }

  function demoButtons() {
    return state.demos.map((demo) => `
      <button type="button" class="demo-btn" data-demo="${escapeHtml(demo.id)}" aria-pressed="${demo.id === state.demo}">
        <strong>${escapeHtml(demo.name)}</strong>
        <span>${escapeHtml(demo.surface)}</span>
      </button>`).join("");
  }

  function renderBench(demo) {
    return `<div class="bench">
      <div class="rail-band"><div class="rail" role="toolbar" aria-label="Demos">${demoButtons()}</div></div>
      <section class="identity">
        <h1>${escapeHtml(demo.name)}</h1>
        <p class="purpose">${escapeHtml(demo.purpose)}</p>
        <div class="measure">
          <div><h2>Jev is asked</h2><p>${escapeHtml(demo.asked)}</p></div>
          <div><h2>Code keeps</h2><p>${escapeHtml(demo.keeps)}</p></div>
          <div><h2>Run</h2>${runCell(demo)}</div>
        </div>
      </section>
      <section class="analysis" aria-label="Jev analysis">
        <div class="analysis-head">
          <h2>Jev analysis</h2>
          <p>${escapeHtml(demo.trace_caption)} Blank fields are not a recorded Jev response. The API key stays on the local server.</p>
        </div>
        <div class="call">
          ${helperButtons(demo)}
          ${rawBlock(ENDPOINT, demo.request, "")}
          ${rawBlock("Response shape", demo.response, "")}
        </div>
      </section>
    </div>`;
  }

  function markHelpers() {
    let marked = null;
    document.querySelectorAll("[data-path]").forEach((line) => {
      const on = line.dataset.path === state.help;
      line.classList.toggle("mark", on);
      if (on) marked = line;
    });
    document.querySelectorAll("[data-help]").forEach((button) => {
      button.setAttribute("aria-pressed", button.dataset.help === state.help ? "true" : "false");
    });
    if (marked) marked.scrollIntoView({ block: "nearest" });
  }

  function bind() {
    document.querySelectorAll("[data-demo]").forEach((button) => {
      button.addEventListener("click", () => {
        state.demo = button.dataset.demo;
        state.help = "";
        render();
      });
    });
    document.querySelectorAll("[data-help]").forEach((button) => {
      button.addEventListener("click", () => {
        state.help = state.help === button.dataset.help ? "" : button.dataset.help;
        markHelpers();
      });
    });
  }

  function render() {
    const demo = currentDemo();
    stage.innerHTML = renderBench(demo);
    statusEl.textContent = demo.name;
    document.title = `${demo.name} · Jev Lab demos`;
    writeUrl();
    bind();
    if (booted && lastDemo !== demo.id) {
      const analysis = stage.querySelector(".analysis");
      if (analysis) analysis.classList.add("settle");
    }
    lastDemo = demo.id;
    booted = true;
    markHelpers();
  }

  function showError(message) {
    stage.innerHTML = `<p class="error">${escapeHtml(message)}</p>`;
    statusEl.textContent = "Catalog failed.";
  }

  fetch(demosUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Could not load the demo catalog (${response.status}). Reload the page to retry.`);
      }
      return response.json();
    })
    .then((payload) => {
      if (!payload || !Array.isArray(payload.demos) || !payload.demos.length) {
        throw new Error("The demo catalog was empty. Reload the page to retry.");
      }
      state.demos = payload.demos;
      readUrl();
      render();
    })
    .catch((error) => {
      const detail = error && error.message ? error.message : "Could not load the demo catalog.";
      const message = /reload/i.test(detail)
        ? detail
        : `${detail} Reload the page to retry.`;
      showError(message);
    });
})();
