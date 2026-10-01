
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
const $ = (id) => document.getElementById(id);
const svg = $("venue-map");
const ns = "http://www.w3.org/2000/svg";
const state = {
  scenario: null,
  plan: null,
  crews: [],
  mode: "fixture",
  time: 0,
  playing: false,
  speed: 5,
  lastFrame: 0,
  selected: null,
  request: 0,
  previousMean: null,
  drag: null,
  keyboardTimer: null,
};
const specialtyName = (value) =>
  value === "none"
    ? "Review needed"
    : value
      ? value[0].toUpperCase() + value.slice(1)
      : "Unknown";
const stamp = (seconds) =>
  `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );
function node(tag, attrs = {}, parent) {
  const el = document.createElementNS(ns, tag);
  for (const [key, value] of Object.entries(attrs))
    el.setAttribute(key, String(value));
  if (parent) parent.append(el);
  return el;
}
function assignmentFor(id) {
  return state.plan?.assignments.find((a) => a.report_id === id);
}
function reportPosition(report, time, assignment) {
  const stop = assignment?.dispatch_at ?? Infinity;
  const targetTime = Math.min(time, stop);
  const fraction =
    report.move_until > report.at
      ? clamp((targetTime - report.at) / (report.move_until - report.at), 0, 1)
      : 1;
  return {
    x: report.x + (report.end_x - report.x) * fraction,
    y: report.y + (report.end_y - report.y) * fraction,
  };
}
function crewPosition(crew, time) {
  const moves = state.plan.assignments
    .filter((a) => a.crew_id === crew.id && a.dispatch_at !== null)
    .sort((a, b) => a.dispatch_at - b.dispatch_at);
  let position = { x: crew.x, y: crew.y };
  for (const move of moves) {
    if (time < move.dispatch_at) break;
    if (time < move.arrive_at) {
      const fraction = clamp(
        (time - move.dispatch_at) / (move.arrive_at - move.dispatch_at),
        0,
        1,
      );
      return {
        x: move.from_x + (move.to_x - move.from_x) * fraction,
        y: move.from_y + (move.to_y - move.from_y) * fraction,
      };
    }
    position = { x: move.to_x, y: move.to_y };
  }
  return position;
}
function svgPoint(event) {
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const transformed = point.matrixTransform(svg.getScreenCTM().inverse());
  return {
    x: clamp(Math.round(transformed.x), 24, 976),
    y: clamp(Math.round(transformed.y), 24, 676),
  };
}
function setNote(message, error = false) {
  $("plan-note").textContent = message;
  $("plan-note").classList.toggle("error", error);
}
function setPlaying(value) {
  state.playing = value;
  state.lastFrame = performance.now();
  $("play-text").textContent = value ? "Pause" : "Play";
  $("play-button").setAttribute(
    "aria-label",
    value ? "Pause replay" : "Play replay",
  );
  $("play-icon").innerHTML = value
    ? '<path d="M8 5v14M16 5v14"/>'
    : '<path d="m8 5 11 7-11 7Z"/>';
}
function renderMap() {
  if (!state.plan) return;
  const routes = $("route-layer"),
    reports = $("report-layer"),
    crews = $("crew-layer");
  routes.replaceChildren();
  for (const assignment of state.plan.assignments) {
    if (
      !assignment.crew_id ||
      assignment.dispatch_at == null ||
      state.time < assignment.dispatch_at ||
      state.time >= assignment.arrive_at
    )
      continue;
    const crew = state.crews.find((c) => c.id === assignment.crew_id);
    if (!crew) continue;
    const pos = crewPosition(crew, state.time);
    node(
      "line",
      {
        x1: pos.x,
        y1: pos.y,
        x2: assignment.to_x,
        y2: assignment.to_y,
        class: "route",
      },
      routes,
    );
  }
  for (const report of state.plan.reports) {
    let group = [...reports.children].find((el) => el.dataset.id === report.id);
    if (!group) {
      group = node(
        "g",
        { class: "report-pin", role: "button", tabindex: "0" },
        reports,
      );
      group.dataset.id = report.id;
      node("circle", { class: "outer", r: 15 }, group);
      node("circle", { class: "inner", r: 3 }, group);
      group.addEventListener("click", () => selectReport(report.id));
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectReport(report.id);
        }
      });
    }
    const assignment = assignmentFor(report.id),
      pos = reportPosition(report, state.time, assignment);
    const resolved =
      assignment?.clear_at != null && state.time >= assignment.clear_at;
    group.style.display = state.time < report.at ? "none" : "";
    group.classList.toggle("selected", state.selected === report.id);
    group.classList.toggle("resolved", resolved);
    group.setAttribute("transform", `translate(${pos.x} ${pos.y})`);
    group.setAttribute(
      "aria-label",
      `${report.title}, ${resolved ? "resolved" : "active"}`,
    );
  }
  for (const crew of state.crews) {
    let group = [...crews.children].find((el) => el.dataset.id === crew.id);
    if (!group) {
      group = node(
        "g",
        { class: "crew-pin", role: "button", tabindex: "0" },
        crews,
      );
      group.dataset.id = crew.id;
      node("circle", { class: "hit-area", r: 60 }, group);
      node("circle", { class: "halo", r: 30 }, group);
      node("circle", { r: 22 }, group);
      const label = node("text", { y: 1 }, group);
      label.textContent =
        crew.id === "welfare"
          ? "W"
          : crew.id === "ops"
            ? "O"
            : crew.id.replace("ed_", "").replace("ec_", "").toUpperCase();
      group.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        event.preventDefault();
        setPlaying(false);
        state.time = 0;
        const position = svgPoint(event);
        state.drag = { id: crew.id, position, pointerId: event.pointerId };
        group.setPointerCapture(event.pointerId);
        renderMap();
        group.classList.add("dragging");
        group.setAttribute(
          "transform",
          `translate(${position.x} ${position.y})`,
        );
        renderClock();
        renderDetails();
      });
      group.addEventListener("pointermove", (event) => {
        if (
          state.drag?.id !== crew.id ||
          state.drag.pointerId !== event.pointerId
        )
          return;
        state.drag.position = svgPoint(event);
        group.setAttribute(
          "transform",
          `translate(${state.drag.position.x} ${state.drag.position.y})`,
        );
      });
      group.addEventListener("pointerup", (event) => {
        if (state.drag?.id !== crew.id) return;
        const position = svgPoint(event);
        state.drag = null;
        const current = state.crews.find((c) => c.id === crew.id);
        current.x = position.x;
        current.y = position.y;
        group.classList.remove("dragging");
        renderMap();
        requestPlan();
      });
      group.addEventListener("pointercancel", () => {
        state.drag = null;
        group.classList.remove("dragging");
        renderMap();
      });
      group.addEventListener("keydown", (event) => {
        const delta = {
          ArrowLeft: [-20, 0],
          ArrowRight: [20, 0],
          ArrowUp: [0, -20],
          ArrowDown: [0, 20],
        }[event.key];
        if (!delta) return;
        event.preventDefault();
        setPlaying(false);
        state.time = 0;
        const current = state.crews.find((c) => c.id === crew.id);
        current.x = clamp(current.x + delta[0], 24, 976);
        current.y = clamp(current.y + delta[1], 24, 676);
        renderClock();
        renderMap();
        renderDetails();
        clearTimeout(state.keyboardTimer);
        state.keyboardTimer = setTimeout(requestPlan, 180);
      });
    }
    const pos =
      state.drag?.id === crew.id
        ? state.drag.position
        : crewPosition(crew, state.time);
    group.classList.toggle("off", !crew.enabled);
    group.classList.add(`specialty-${crew.specialty}`);
    group.setAttribute("transform", `translate(${pos.x} ${pos.y})`);
    group.setAttribute(
      "aria-label",
      `${crew.name}, ${crew.specialty} crew, ${crew.enabled ? "enabled" : "unavailable"}. Drag or use arrow keys to change starting position.`,
    );
  }
}
function statusFor(report, assignment) {
  if (state.time < report.at) return "Upcoming";
  if (assignment?.status === "review") return "Review";
  if (assignment?.status === "unassigned") return "Unassigned";
  if (
    assignment?.clear_at !== null &&
    assignment?.clear_at !== undefined &&
    state.time >= assignment.clear_at
  )
    return "Cleared";
  if (
    assignment?.arrive_at !== null &&
    assignment?.arrive_at !== undefined &&
    state.time >= assignment.arrive_at
  )
    return "On scene";
  if (
    assignment?.dispatch_at !== null &&
    assignment?.dispatch_at !== undefined &&
    state.time >= assignment.dispatch_at
  )
    return "Responding";
  return "Queued";
}
function selectReport(id) {
  state.selected = id;
  renderDetails();
  renderMap();
}
function renderDetails() {
  if (!state.plan) return;
  const list = $("report-list");
  const active = state.plan.reports.filter(
    (r) =>
      state.time >= r.at && statusFor(r, assignmentFor(r.id)) !== "Cleared",
  ).length;
  $("incident-status").textContent = `${active} active at ${stamp(state.time)}`;
  $("report-count").textContent = state.plan.reports.length;
  for (const report of state.plan.reports) {
    const assignment = assignmentFor(report.id);
    let row = [...list.children].find((el) => el.dataset.id === report.id);
    if (!row) {
      row = document.createElement("button");
      row.type = "button";
      row.dataset.id = report.id;
      row.addEventListener("click", () => selectReport(report.id));
      list.append(row);
    }
    row.className = `report-row${state.selected === report.id ? " selected" : ""}`;
    row.innerHTML = `<span class="at">${stamp(report.at)}</span><span><strong>${esc(report.title)}</strong><small>${esc(report.zone)}</small></span><span class="pill ${assignment?.status === "review" ? "review" : state.time >= report.at && statusFor(report, assignment) !== "Cleared" ? "live" : ""}">${statusFor(report, assignment)}</span>`;
  }
  const report =
      state.plan.reports.find((r) => r.id === state.selected) ||
      state.plan.reports[0],
    detail = $("report-detail");
  if (!report) {
    detail.replaceChildren();
    return;
  }
  const judgment = state.plan.judgments[report.id],
    assignment = assignmentFor(report.id),
    crew = state.plan.crews.find((c) => c.id === assignment?.crew_id);
  const escalation =
    assignment?.escalation === "escalate"
      ? "Supervisor escalation"
      : assignment?.escalation === "review"
        ? "Safety review"
        : "No escalation supported";
  const detailKey = `${report.id}:${state.plan.mode}:${assignment?.crew_id}:${assignment?.status}:${assignment?.escalation}`;
  if (detail.dataset.key === detailKey) return;
  detail.dataset.key = detailKey;
  detail.innerHTML = `<div class="detail-title">${esc(report.title)}</div><p class="detail-copy">${esc(report.text)}</p><div class="fact-grid"><div class="fact"><label>Urgency</label><strong>${judgment ? `${Number(judgment.urgency).toFixed(1)} / 3` : "Unavailable"}</strong></div><div class="fact"><label>Suggested team</label><strong>${specialtyName(judgment?.team)}</strong></div><div class="fact"><label>Assignment</label><strong>${crew ? esc(crew.name) : esc(assignment?.status === "review" ? "Needs review" : "None")}</strong></div><div class="fact"><label>Response</label><strong>${assignment?.arrive_at != null && assignment?.dispatch_at != null ? `${Math.round(assignment.arrive_at - report.at)} sec` : esc(assignment?.reason || "Pending")}</strong></div></div><div class="evidence">Team confidence ${judgment ? Math.round(judgment.team_confidence * 100) + "%" : "—"} · Urgency confidence ${judgment ? Math.round(judgment.urgency_confidence * 100) + "%" : "—"}<br>Safety evidence ${judgment ? Math.round(judgment.evidence * 100) + "%" : "—"} · ${escalation}</div>`;
  appendInspection(detail, state.plan.inspection);
}
function renderCrew() {
  const list = $("crew-list");
  list.replaceChildren();
  $("crew-count").textContent = state.crews.length;
  for (const crew of state.crews) {
    const row = document.createElement("div");
    row.className = "crew-row";
    row.innerHTML = `<span class="crew-swatch"></span><span><strong>${esc(crew.name)}</strong><small>${esc(crew.specialty)} · <span class="crew-state"></span></small></span><label><input type="checkbox" ${crew.enabled ? "checked" : ""} aria-label="${esc(crew.name)} available">Available</label>`;
    row.querySelector("input").addEventListener("change", (event) => {
      state.crews.find((c) => c.id === crew.id).enabled = event.target.checked;
      setPlaying(false);
      state.time = 0;
      renderClock();
      renderMap();
      requestPlan();
    });
    list.append(row);
  }
  updateCrewStates();
}
function updateCrewStates() {
  for (const [index, crew] of state.crews.entries()) {
    const assignment = state.plan?.assignments.find(
      (a) =>
        a.crew_id === crew.id &&
        a.dispatch_at != null &&
        state.time >= a.dispatch_at &&
        state.time < a.clear_at,
    );
    const status = !crew.enabled
      ? "Off duty"
      : !assignment
        ? "Idle"
        : state.time < assignment.arrive_at
          ? "Responding"
          : "On scene";
    const label = $("crew-list").children[index]?.querySelector(".crew-state");
    if (label) label.textContent = status;
  }
}
function renderClock() {
  if (!state.plan) return;
  const duration = state.plan.duration;
  $("time-label").textContent = `${stamp(state.time)} / ${stamp(duration)}`;
  $("timeline").max = String(Math.ceil(duration));
  $("timeline").value = String(Math.round(state.time));
  $("timeline").style.background =
    `linear-gradient(to right,#c95038 ${(state.time / duration) * 100}%,#d8e3d5 ${(state.time / duration) * 100}%)`;
}
function renderTicks() {
  const target = $("timeline-events");
  target.replaceChildren();
  if (!state.plan) return;
  for (const report of state.plan.reports) {
    const tick = document.createElement("i");
    tick.style.left = `${(report.at / state.plan.duration) * 100}%`;
    target.append(tick);
  }
  for (const assignment of state.plan.assignments) {
    if (assignment.clear_at == null) continue;
    const tick = document.createElement("i");
    tick.className = "clear";
    tick.style.left = `${(assignment.clear_at / state.plan.duration) * 100}%`;
    target.append(tick);
  }
}
function render() {
  renderClock();
  renderMap();
  renderDetails();
  renderCrew();
}
function comparison() {
  const current = state.plan?.summary;
  const previous = state.previousSummary;
  if (!current || !previous) return "Move a crew to compare response times";
  const coverage = current.assigned - previous.assigned;
  if (coverage)
    return `${Math.abs(coverage)} ${coverage > 0 ? "more" : "fewer"} reports assigned than previous plan`;
  if (!current.assigned) return "No reports assigned in either plan";
  const delta = current.mean_response_seconds - previous.mean_response_seconds;
  if (Math.abs(delta) < 0.5) return "Mean response unchanged";
  return `Mean response ${Math.round(Math.abs(delta))} sec ${delta < 0 ? "faster" : "slower"} than previous plan`;
}
async function requestPlan(mode = state.mode, requestedCrews = null) {
  if (requestedCrews) state.crews = requestedCrews.map((c) => ({ ...c }));
  if (!state.scenario) return;
  clearTimeout(state.keyboardTimer);
  const crewSnapshot = state.crews.map((c) => ({ ...c }));
  const request = ++state.request;
  const button = $("source-button");
  button.disabled = true;
  setNote(`Building ${mode === "live" ? "live Jev" : "fixture"} plan…`);
  try {
    const response = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode,
        crews: crewSnapshot.map(({ id, x, y, enabled }) => ({
          id,
          x,
          y,
          enabled,
        })),
      }),
    });
    const data = await response.json();
    if (!response.ok)
      throw new Error(data.error || `Plan request failed (${response.status})`);
    if (request !== state.request) return;
    state.previousSummary =
      state.plan?.mode === data.mode ? state.plan.summary : null;
    state.plan = data;
    state.crews = data.crews.map((c) => ({ ...c }));
    delete $("report-detail").dataset.key;
    state.mode = data.mode;
    state.time = 0;
    setPlaying(false);
    state.selected =
      state.selected && data.reports.some((r) => r.id === state.selected)
        ? state.selected
        : data.reports[0]?.id;
    $("source-badge").textContent =
      data.mode === "live"
        ? `Live Jev · synthetic reports (${data.model || "model unknown"})`
        : "Fixture judgments · synthetic reports";
    button.textContent =
      data.mode === "live" ? "Use fixture judgments" : "Use live Jev";
    button.hidden = data.mode !== "live" && !state.scenario.live_available;
    button.disabled = false;
    delete button.dataset.retryMode;
    $("comparison").textContent = comparison();
    setNote(
      `${data.summary.assigned} assigned · ${data.summary.unassigned} unassigned. Reports are synthetic.`,
    );
    renderTicks();
    render();
  } catch (error) {
    if (request !== state.request) return;
    button.disabled = false;
    state.retryCrews = crewSnapshot;
    if (state.plan) {
      state.crews = state.plan.crews.map((c) => ({ ...c }));
      render();
    }
    setNote(
      `${error.message}. Previous plan remains visible. Retry the requested source.`,
      true,
    );
    button.textContent =
      mode === "live" ? "Retry live Jev" : "Retry fixture plan";
    button.hidden = false;
    button.dataset.retryMode = mode;
  }
}
function tick(now) {
  if (state.playing && state.plan) {
    const elapsed = ((now - state.lastFrame) / 1000) * state.speed;
    state.time = clamp(state.time + elapsed, 0, state.plan.duration);
    if (state.time >= state.plan.duration) setPlaying(false);
    renderClock();
    renderMap();
    if (Math.floor(state.time) !== Math.floor(state.time - elapsed)) {
      renderDetails();
      updateCrewStates();
    }
  }
  state.lastFrame = now;
  requestAnimationFrame(tick);
}
function tab(name) {
  const isReports = name === "reports";
  $("tab-reports").classList.toggle("active", isReports);
  $("tab-crew").classList.toggle("active", !isReports);
  $("tab-reports").setAttribute("aria-selected", String(isReports));
  $("tab-crew").setAttribute("aria-selected", String(!isReports));
  $("reports-panel").hidden = !isReports;
  $("crew-panel").hidden = isReports;
}
$("tab-reports").addEventListener("click", () => tab("reports"));
$("tab-crew").addEventListener("click", () => tab("crew"));
for (const name of ["reports", "crew"])
  $("tab-" + name).addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const next =
      event.key === "Home"
        ? "reports"
        : event.key === "End"
          ? "crew"
          : name === "reports"
            ? "crew"
            : "reports";
    tab(next);
    $("tab-" + next).focus();
  });
$("play-button").addEventListener("click", () => {
  if (!state.plan) return;
  if (state.time >= state.plan.duration) state.time = 0;
  setPlaying(!state.playing);
  render();
});
$("reset-button").addEventListener("click", () => {
  setPlaying(false);
  state.time = 0;
  render();
});
$("timeline").addEventListener("input", (event) => {
  setPlaying(false);
  state.time = Number(event.target.value);
  renderClock();
  renderMap();
  renderDetails();
  updateCrewStates();
});
$("speed").addEventListener("change", (event) => {
  state.speed = Number(event.target.value);
});
$("source-button").addEventListener("click", () =>
  requestPlan(
    $("source-button").dataset.retryMode ||
      (state.mode === "live" ? "fixture" : "live"),
    $("source-button").dataset.retryMode ? state.retryCrews : null,
  ),
);
async function init() {
  try {
    const response = await fetch("/api/scenario");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Scenario unavailable");
    state.scenario = data;
    state.crews = data.crews.map((c) => ({ ...c }));
    $("source-button").hidden = !data.live_available;
    await requestPlan("fixture");
  } catch (error) {
    setNote(`${error.message}. Reload to retry.`, true);
  }
}
requestAnimationFrame(tick);
init();
