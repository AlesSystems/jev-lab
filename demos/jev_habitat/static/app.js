const $ = id => document.getElementById(id);
const labels = ['Off', 'Dim', 'Reading', 'Bright'];
const actions = { lights: 'Set lights', music_on: 'Turn music on', music_off: 'Turn music off', blinds_open: 'Open blinds', blinds_close: 'Close blinds', no_change: 'No change' };
let config, rooms, selected = 'living', revision = 0, proposal = null, pending = false;
const clone = value => JSON.parse(JSON.stringify(value));
const fmt = value => Number(value).toFixed(2);
const current = () => rooms[selected];
const snapshot = () => ({ text: $('request-text').value, room: selected, devices: clone(current()), mode: $('mode').value });
function invalidate(message = 'Request or room changed. Evaluate again.') {
  revision++;
  proposal = null;
  $('result').hidden = true;
  $('empty-result').hidden = false;
  $('empty-result').textContent = message;
  $('status').textContent = message;
}
function renderRoom() {
  document.querySelectorAll('.room').forEach(el => {
    const state = rooms[el.dataset.room];
    el.classList.toggle('selected', el.dataset.room === selected);
    el.classList.toggle('blinds-closed', state.blinds === 'closed');
    el.classList.toggle('music-on', state.music);
    el.style.setProperty('--glow', (state.lights * .24).toFixed(2));
    el.setAttribute('aria-pressed', String(el.dataset.room === selected));
    el.querySelector('.room-mini').textContent = `${labels[state.lights]} · ${state.music ? 'Music on' : 'Quiet'} · Blinds ${state.blinds}`;
  });
  $('room-label').textContent = config.rooms[selected].name;
  $('lights').value = current().lights;
  $('lights-value').textContent = `${labels[current().lights]} · ${current().lights}`;
  $('music').textContent = current().music ? 'On' : 'Off';
  $('music').setAttribute('aria-pressed', String(current().music));
  $('blinds').textContent = current().blinds === 'open' ? 'Open' : 'Closed';
  $('blinds').setAttribute('aria-pressed', String(current().blinds === 'open'));
}
function canApply(result, threshold) {
  const a = result.answers;
  return result.action !== 'no_change' &&
    a.applicable.noul >= threshold &&
    a.action.confidence >= threshold &&
    (result.action !== 'lights' || a.brightness.confidence >= threshold);
}
function renderPolicy() {
  const threshold = Number($('threshold').value);
  $('threshold-value').textContent = fmt(threshold);
  if (!proposal) return;
  const result = proposal.result, a = result.answers;
  const usable = canApply(result, threshold) && !proposal.applied;
  $('apply').disabled = !usable;
  $('apply').textContent = proposal.applied ? 'Applied to room' : result.action === 'no_change' ? 'No action to apply' : 'Apply to room';
  const conditions = [`applicability ${fmt(a.applicable.noul)}`, `action confidence ${fmt(a.action.confidence)}`];
  if (result.action === 'lights') conditions.push(`brightness confidence ${fmt(a.brightness.confidence)}`);
  $('rule-explanation').textContent = result.action === 'no_change' ? 'Code rule: no_change always holds the room.' : proposal.applied ? 'This proposal was applied once. Evaluate again for another change.' : `Code rule: ${conditions.join(' · ')} must each reach ${fmt(threshold)}. ${usable ? 'Ready to apply.' : 'Held below your threshold.'}`;
  $('result-title').textContent = result.action === 'no_change' ? 'Room stays as it is' : `${actions[result.action]}${result.action === 'lights' ? ` → ${labels[result.target]}` : ''}`;
  $('result-summary').textContent = usable ? 'Ready when you are. Apply changes only this browser simulation.' : result.action === 'no_change' ? 'No single supported action was selected.' : proposal.applied ? 'The simulated room now shows the change.' : 'The proposal is held. Lower the local threshold to inspect a different policy.';
}
function showResult(result, elapsed) {
  proposal = { result, applied: false };
  $('result').hidden = false;
  $('empty-result').hidden = true;
  $('result-source').textContent = result.source;
  $('choice').textContent = actions[result.action];
  $('choice-detail').textContent = `Confidence ${fmt(result.answers.action.confidence)} · ${Object.entries(result.answers.action.probabilities).map(([key, value]) => `${key} ${fmt(value)}`).join(' / ')}`;
  $('score').textContent = `${Number(result.answers.brightness.score).toFixed(2)} / 3`;
  $('score-detail').textContent = result.action === 'lights' ? `Brightness, not certainty. Confidence ${fmt(result.answers.brightness.confidence)}.` : `Speculative brightness answer, unused by this ${result.action} decision.`;
  $('noul').textContent = fmt(result.answers.applicable.noul);
  $('noul-detail').textContent = 'Probability that one actionable change applies to this room.';
  $('raw-request').textContent = JSON.stringify(result.inspection.request, null, 2);
  $('raw-response').textContent = JSON.stringify(result.inspection.response, null, 2);
  $('telemetry').textContent = `· ${Math.round(elapsed)} ms locally${result.usage ? ` · ${result.usage.input_tokens} input / ${result.usage.output_tokens} output tokens` : ''}`;
  renderPolicy();
  $('status').textContent = `${result.source} returned. Review the rule, then apply if ready.`;
}
async function evaluate() {
  if (pending) return;
  const input = snapshot(), captured = ++revision;
  proposal = null;
  $('result').hidden = true;
  $('empty-result').hidden = false;
  $('empty-result').textContent = 'Evaluating three questions over one room snapshot…';
  $('status').textContent = `Evaluating ${input.mode === 'fixture' ? 'prepared fixture' : 'Live Jev'}…`;
  $('evaluate').disabled = true;
  pending = true;
  const start = performance.now();
  try {
    const response = await fetch('/api/evaluate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) });
    const body = await response.json();
    if (captured !== revision || input.room !== selected || JSON.stringify(input.devices) !== JSON.stringify(current())) return;
    if (!response.ok) throw new Error(body.error || 'Evaluation failed. Retry.');
    showResult(body, performance.now() - start);
  } catch (error) {
    if (captured !== revision) return;
    $('empty-result').textContent = error.message;
    $('status').textContent = error.message;
  } finally {
    pending = false;
    $('evaluate').disabled = false;
  }
}
function apply() {
  if (!proposal || proposal.applied || !canApply(proposal.result, Number($('threshold').value))) return;
  const r = proposal.result;
  if (r.action === 'lights') current().lights = r.target;
  if (r.action === 'music_on') current().music = true;
  if (r.action === 'music_off') current().music = false;
  if (r.action === 'blinds_open') current().blinds = 'open';
  if (r.action === 'blinds_close') current().blinds = 'closed';
  proposal.applied = true;
  renderRoom();
  renderPolicy();
  $('status').textContent = 'Applied to the simulated room. Evaluate again for another change.';
}
async function init() {
  const response = await fetch('/api/config');
  if (!response.ok) throw new Error('Could not load room catalog. Reload the page.');
  config = await response.json();
  rooms = Object.fromEntries(Object.entries(config.rooms).map(([key, room]) => [key, clone(room.initial)]));
  $('request-text').value = config.examples[0].text;
  for (const example of config.examples) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'example';
    button.textContent = example.text;
    button.addEventListener('click', () => { selected = example.room; $('request-text').value = example.text; renderRoom(); invalidate('Prepared request selected. Evaluate to see its illustrative answers.'); });
    $('examples').append(button);
  }
  document.querySelectorAll('.room').forEach(button => button.addEventListener('click', () => { if (selected !== button.dataset.room) { selected = button.dataset.room; renderRoom(); invalidate(); } }));
  $('request-text').addEventListener('input', () => invalidate('Request edited. Evaluate with Live Jev; prepared fixtures require exact text and state.'));
  $('mode').addEventListener('change', () => { invalidate(); $('mode-note').textContent = $('mode').value === 'fixture' ? 'Illustrative prepared answers. Exact example, room and original device state required.' : config.liveAvailable ? 'Live Jev uses the server key and returns model answers.' : 'Live Jev needs TYPESAFE_API_KEY on the server.'; });
  $('mode-note').textContent = 'Illustrative prepared answers. Exact example, room and original device state required.';
  $('lights').addEventListener('input', () => { current().lights = Number($('lights').value); renderRoom(); invalidate('Room state changed. Evaluate again.'); });
  $('music').addEventListener('click', () => { current().music = !current().music; renderRoom(); invalidate('Room state changed. Evaluate again.'); });
  $('blinds').addEventListener('click', () => { current().blinds = current().blinds === 'open' ? 'closed' : 'open'; renderRoom(); invalidate('Room state changed. Evaluate again.'); });
  $('reset').addEventListener('click', () => { rooms[selected] = clone(config.rooms[selected].initial); renderRoom(); invalidate('Room reset. Evaluate again.'); });
  $('threshold').addEventListener('input', renderPolicy);
  $('evaluate').addEventListener('click', evaluate);
  $('apply').addEventListener('click', apply);
  renderRoom();
}
init().catch(error => { $('status').textContent = error.message; $('evaluate').disabled = true; });
