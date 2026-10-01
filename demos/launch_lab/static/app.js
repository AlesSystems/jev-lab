const $ = (id) => document.getElementById(id);
const state = { releases: {}, releaseId: 'friday', selected: new Set(), assessment: null, revision: 0, request: null, drawerFrom: null, deadline: 0 };
const labels = { pass: 'Passed', fail: 'Failed', flaky: 'Flaky', missing: 'Missing', unverified: 'Unverified', explained: 'Explained' };
const checkLabels = { browser: 'Browser journey', load: 'Load test', rollback: 'Rollback verification', 'payment retry': 'Payment retry', 'mobile upload': 'Mobile upload' };
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
function release() { return state.releases[state.releaseId]; }
function markStale() {
  state.revision += 1;
  state.request?.abort();
  state.request = null;
  $('assess').disabled = false;
  $('assess').innerHTML = 'Ask Jev to reassess <span aria-hidden="true">→</span>';
  if (state.assessment) $('feedback').textContent = 'Evidence changed. Reassess to update the judgment.';
  state.assessment = null;
  $('assessment').replaceChildren();
  $('assessment').hidden = true;
  $('readiness').className = 'readiness';
  $('readiness').innerHTML = '<span class="status-mark"></span><strong>Awaiting reassessment</strong><p>Ask Jev to judge the current evidence.</p>';
}
function setRelease(id) {
  if (!state.releases[id]) return;
  markStale();
  state.releaseId = id;
  state.selected = new Set(release().evidence.map((item) => item.id));
  state.assessment = null;
  state.deadline = Date.now() + release().hours * 3600000;
  $('assessment').hidden = true;
  $('readiness').className = 'readiness';
  $('readiness').innerHTML = '<span class="status-mark"></span><strong>Awaiting assessment</strong><p>Choose evidence and ask Jev.</p>';
  $('feedback').textContent = '';
  closeDrawer();
  render();
  updateClock();
}
function updateClock() {
  const seconds = Math.max(0, Math.floor((state.deadline - Date.now()) / 1000));
  const hours = Math.floor(seconds / 3600);
  $('countdown').textContent = `${String(hours).padStart(2, '0')}:${String(Math.floor(seconds % 3600 / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}
function sparkline(values) {
  const low = Math.min(...values), high = Math.max(...values), span = high - low || 1;
  const points = values.map((v, i) => `${i * 54},${59 - (v - low) / span * 48}`).join(' ');
  return `<svg class="sparkline" viewBox="0 0 270 70" preserveAspectRatio="none" aria-hidden="true"><path d="M0 60H270" class="chart-base"/><polyline points="${points}"/></svg>`;
}
function render() {
  const current = release();
  const focusedRelease = document.activeElement?.matches('#releases button') ? document.activeElement.dataset.release : null;
  $('releases').innerHTML = Object.entries(state.releases).map(([id, item]) => `<button type="button" class="release-tab ${id === state.releaseId ? 'active' : ''}" aria-pressed="${id === state.releaseId}" data-release="${id}">${escapeHTML(item.name)}</button>`).join('');
  if (focusedRelease) $('releases').querySelector(`[data-release="${focusedRelease}"]`)?.focus();
  $('release-name').textContent = current.name;
  $('release-summary').textContent = current.summary;
  $('metrics').innerHTML = current.metrics.map((metric) => `<button class="metric" type="button" data-metric="${metric.id}" aria-label="Inspect ${escapeHTML(metric.label)}"><span class="metric-label">${escapeHTML(metric.label)}</span><strong>${metric.values.at(-1)}<small>${escapeHTML(metric.unit)}</small></strong>${sparkline(metric.values)}<span class="metric-hint">View test results and notes <span aria-hidden="true">↗</span></span></button>`).join('');
  const focusedEvidence = document.activeElement?.matches('#evidence input') ? document.activeElement.value : null;
  $('evidence-count').textContent = `${state.selected.size} of ${current.evidence.length} included`;
  $('evidence').innerHTML = current.evidence.map((item) => `<label class="evidence-card ${state.selected.has(item.id) ? 'chosen' : ''}"><input type="checkbox" value="${item.id}" ${state.selected.has(item.id) ? 'checked' : ''}><span class="evidence-copy"><span class="evidence-title">${escapeHTML(item.title)} <span class="tag ${item.status}">${labels[item.status]}</span></span><span class="evidence-text">${escapeHTML(item.text)}</span></span></label>`).join('');
  if (focusedEvidence) $('evidence').querySelector(`input[value="${focusedEvidence}"]`)?.focus();
  $('checklist').innerHTML = current.evidence.filter((item) => item.required).map((item) => `<div class="check-row"><span class="check-icon ${item.status}" aria-hidden="true">${item.status === 'pass' ? '✓' : '!'}</span><div><strong>${escapeHTML(checkLabels[item.check] || item.title)}</strong><span>${labels[item.status]} · required</span></div></div>`).join('');
}
function showDrawer(id) {
  const metric = release().metrics.find((item) => item.id === id);
  if (!metric) return;
  state.drawerFrom = document.activeElement;
  $('drawer-title').textContent = metric.label;
  $('drawer-note').textContent = metric.note;
  const related = release().evidence.filter((item) => metric.related.includes(item.id));
  $('drawer-body').innerHTML = `<div class="drawer-data"><span>Six synthetic observations</span><strong>${metric.values.join(' · ')} ${escapeHTML(metric.unit)}</strong></div><h3>Underlying results and notes</h3>${related.map((item) => `<article class="drawer-item"><div><strong>${escapeHTML(item.title)}</strong><span class="tag ${item.status}">${labels[item.status]}</span></div><p>${escapeHTML(item.text)}</p><small>${state.selected.has(item.id) ? 'Included in assessment' : 'Excluded from assessment'}</small></article>`).join('')}`;
  $('drawer').hidden = false;
  $('drawer-backdrop').hidden = false;
  document.body.classList.add('drawer-open');
  $('drawer-close').focus();
}
function closeDrawer() {
  if ($('drawer').hidden) return;
  $('drawer').hidden = true;
  $('drawer-backdrop').hidden = true;
  document.body.classList.remove('drawer-open');
  state.drawerFrom?.focus();
}
function renderAssessment(result) {
  const status = result.status;
  $('readiness').className = `readiness ${status.replace(' ', '-')}`;
  const heading = status === 'blocked' ? 'Hold the release' : status === 'supported' ? 'Evidence supports shipping' : 'More evidence needed';
  const reason = result.blocked_by.length ? `${result.blocked_by.length} required check${result.blocked_by.length === 1 ? '' : 's'} unresolved.` : `${Math.round(result.support * 100)}% ${result.mode === 'live' ? 'Jev' : 'fixture'} support for the claim.`;
  $('readiness').innerHTML = `<span class="status-mark"></span><strong>${heading}</strong><p>${reason}</p>`;
  const scores = Object.entries(result.answers).filter(([id]) => id.startsWith('score_'));
  $('assessment').hidden = false;
  $('assessment').classList.remove('stale');
  $('assessment').innerHTML = `<div class="assessment-head"><h3>Assessment</h3><span class="tag source">${result.mode === 'live' ? 'Live Jev' : 'Offline fixture'}</span></div><p class="claim">“${escapeHTML(release().claim)}”</p><div class="judgment"><span>Claim support</span><strong>${Math.round(result.support * 100)}%</strong></div><div class="judgment"><span>Useful next check</span><strong>${escapeHTML(checkLabels[result.next_check] || 'Targeted reproduction')}</strong></div>${scores.map(([id, answer]) => `<div class="judgment"><span>${escapeHTML(release().evidence.find((item) => item.id === id.slice(6))?.title || id)}</span><strong>${Number(answer.score).toFixed(1)} / 3 concern</strong></div>`).join('')}<details><summary>Inspect exact evidence and Jev answers</summary><div class="inspect-label">Input sent to ${result.mode === 'live' ? 'Jev' : 'fixture evaluator'}</div><pre>${escapeHTML(JSON.stringify(result.input, null, 2))}</pre><div class="inspect-label">${result.inspection ? "Exact Jev response" : "Hand-authored fixture answers"} · ${escapeHTML(result.model)}</div><p>${escapeHTML(result.inspection?.note || "No Jev API call occurred. These are illustrative fixture answers; readiness explanations are application rules.")}</p><pre>${escapeHTML(JSON.stringify(result.inspection?.response || result.answers, null, 2))}</pre></details>`;
  $('feedback').textContent = result.mode === 'live' ? 'Live Jev assessment complete.' : 'Offline fixture assessment complete.';
}
async function assess() {
  state.request?.abort();
  const controller = new AbortController();
  state.request = controller;
  const revision = state.revision;
  const payload = { release: state.releaseId, selected: [...state.selected], mode: $('mode').value };
  $('assess').disabled = true;
  $('assess').textContent = 'Assessing…';
  $('feedback').textContent = payload.mode === 'live' ? 'Waiting for live Jev…' : 'Assessing selected evidence…';
  try {
    const response = await fetch('/api/assess', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: controller.signal });
    const result = await response.json();
    if (revision !== state.revision || controller !== state.request) return;
    if (!response.ok) throw new Error(result.error || 'Assessment failed. Try again.');
    state.assessment = result;
    renderAssessment(result);
  } catch (error) {
    if (error.name !== 'AbortError' && revision === state.revision) $('feedback').textContent = `${error.message} Retry when ready.`;
  } finally {
    if (controller === state.request) {
      state.request = null;
      $('assess').disabled = false;
      $('assess').innerHTML = 'Ask Jev to reassess <span aria-hidden="true">→</span>';
    }
  }
}
$('releases').addEventListener('click', (event) => { const button = event.target.closest('[data-release]'); if (button) setRelease(button.dataset.release); });
$('metrics').addEventListener('click', (event) => { const button = event.target.closest('[data-metric]'); if (button) showDrawer(button.dataset.metric); });
$('evidence').addEventListener('change', (event) => { const box = event.target; if (box.type !== 'checkbox') return; box.checked ? state.selected.add(box.value) : state.selected.delete(box.value); markStale(); render(); });
$('mode').addEventListener('change', markStale);
$('assess').addEventListener('click', assess);
$('drawer-close').addEventListener('click', closeDrawer);
$('drawer-backdrop').addEventListener('click', closeDrawer);
document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeDrawer(); if (event.key === 'Tab' && !$('drawer').hidden) { event.preventDefault(); $('drawer-close').focus(); } });
async function boot() {
  try {
    const response = await fetch('/api/config');
    if (!response.ok) throw new Error('Scenario data could not load.');
    const config = await response.json();
    state.releases = config.releases;
    $('mode').querySelector('[value="live"]').disabled = !config.live_available;
    if (!config.live_available) $('mode').querySelector('[value="live"]').textContent = 'Live Jev · add API key';
    setRelease('friday');
    setInterval(updateClock, 1000);
  } catch (error) { $('feedback').textContent = `${error.message} Refresh the page to retry.`; }
}
boot();
