'use strict';
const $ = id => document.getElementById(id);
let config;
const state = {feedback: {version: 0, result: null, picked: new Set()}, release: {version: 0, result: null}};
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function clearResult(kind, message) {
  state[kind].version++;
  state[kind].result = null;
  $('assess-' + kind).disabled = false;
  $(kind + '-status').textContent = message;
  $(kind + '-status').className = 'status';
  $(kind + '-trace').textContent = 'No current assessment. ' + message;
  if (kind === 'feedback') renderSuggestions();
  else renderDecision();
  document.querySelectorAll(kind === 'feedback' ? '.note-result' : '.finding-score').forEach(el => el.remove());
  handoff();
}
function comments() {
  return Array.from(document.querySelectorAll('#comments textarea'), el => ({id: el.dataset.id, text: el.value}));
}
function addNote(text, id) {
  const row = node('div', undefined, 'comment-row');
  const label = node('label', id.replace('c', ''));
  const field = node('textarea');
  field.id = 'note-' + id;
  field.dataset.id = id;
  field.value = text;
  field.maxLength = 500;
  field.setAttribute('aria-label', 'Customer note ' + id.replace('c', ''));
  label.htmlFor = field.id;
  field.addEventListener('input', () => clearResult('feedback', 'Notes changed. Live Jev is required for edited feedback; reset notes to use the fixture.'));
  row.append(label, field);
  $('comments').append(row);
  $('comment-count').textContent = '(' + comments().length + ')';
  $('add-comment').disabled = comments().length >= 12;
}
function loadProduct() {
  const product = config.products[$('product').value];
  state.feedback.picked.clear();
  $('product-description').textContent = product.description;
  $('comments').replaceChildren();
  product.comments.forEach((text, i) => addNote(text, 'c' + (i + 1)));
  clearResult('feedback', 'Original sample notes loaded. Assess to see the illustrative fixture.');
}
function renderSuggestions() {
  if (!config) return;
  const result = state.feedback.result;
  $('suggestions').replaceChildren();
  config.products[$('product').value].suggestions.forEach(suggestion => {
    const row = node('div', undefined, 'suggestion');
    const checkbox = node('input');
    checkbox.type = 'checkbox';
    checkbox.id = 'pick-' + suggestion.id;
    checkbox.checked = state.feedback.picked.has(suggestion.id);
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) state.feedback.picked.add(suggestion.id);
      else state.feedback.picked.delete(suggestion.id);
      handoff();
    });
    const content = node('div');
    const label = node('label', suggestion.name);
    label.htmlFor = checkbox.id;
    content.append(label, node('p', suggestion.claim));
    if (result) {
      const matches = Object.values(result.choices).filter(item => item.suggestion === suggestion.id).length;
      content.append(node('p', Math.round(result.supports[suggestion.id] * 100) + '% claim support · ' + matches + ' matching notes', 'score'));
    } else content.append(node('p', 'No current assessment'));
    row.append(checkbox, content);
    $('suggestions').append(row);
  });
}
function loadRelease() {
  const release = config.releases[$('release').value];
  $('release-description').textContent = release.summary;
  $('evidence').replaceChildren();
  $('checklist').replaceChildren();
  release.evidence.forEach(item => {
    const row = node('div', undefined, 'evidence-row');
    const checkbox = node('input');
    checkbox.type = 'checkbox';
    checkbox.id = 'evidence-' + item.id;
    checkbox.value = item.id;
    checkbox.checked = true;
    checkbox.addEventListener('change', () => clearResult('release', 'Evidence changed. Reassess the current selection.'));
    const content = node('div');
    const label = node('label', item.title);
    label.htmlFor = checkbox.id;
    content.append(label, node('p', item.text), node('span', item.status + (item.required ? ' · required' : ''), 'tag'));
    row.append(checkbox, content);
    $('evidence').append(row);
    if (item.required) {
      const check = node('li', item.check);
      check.append(node('b', item.status.toUpperCase()));
      $('checklist').append(check);
    }
  });
  clearResult('release', 'Sample release loaded. Assess the selected evidence.');
}
function renderDecision() {
  const result = state.release.result;
  const ready = result && result.status === 'supported';
  $('decision').textContent = !result ? 'UNREAD' : ready ? 'READY' : result.status === 'blocked' ? 'HOLD' : 'REVIEW';
  $('decision').parentElement.classList.toggle('ready', Boolean(ready));
  $('decision-copy').textContent = !result ? 'No current assessment. Read the evidence and assess again.' : result.blocked_by.length ? result.blocked_by.length + ' required checks block release, regardless of selected evidence.' : ready ? 'Required checks pass and selected evidence meets the 80% support rule.' : 'Required checks pass, but the selected evidence does not meet the 80% support rule.';
  $('support').textContent = result ? Math.round(result.support * 100) + '%' : '—';
  $('next-check').textContent = result ? result.next_check : '—';
}
function handoff() {
  if (!config) return;
  const product = config.products[$('product').value];
  const picks = product.suggestions.filter(item => state.feedback.picked.has(item.id)).map(item => item.name);
  const release = config.releases[$('release').value];
  $('handoff').textContent = product.name + ' shortlist: ' + (picks.join(', ') || 'nothing selected') + '. ' + (state.feedback.result ? 'Feedback assessed using ' + state.feedback.result.source + '. ' : 'Feedback has no current assessment. ') + release.name + ': ' + $('decision').textContent + '. These independent sample cases are not a linked release plan.';
}
async function assess(kind) {
  clearResult(kind, 'Assessing…');
  const version = state[kind].version;
  $('assess-' + kind).disabled = true;
  const payload = kind === 'feedback' ? {product: $('product').value, comments: comments(), mode: $('feedback-mode').value} : {release: $('release').value, selected: Array.from(document.querySelectorAll('#evidence input:checked'), el => el.value), mode: $('release-mode').value};
  try {
    const response = await fetch('/api/' + kind, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    const result = await response.json();
    if (version !== state[kind].version) return;
    if (!response.ok) throw new Error(result.error || 'Assessment failed. Retry.');
    state[kind].result = result;
    $(kind + '-status').textContent = kind === 'feedback' ? result.source : result.mode === 'live' ? 'Live Jev · ' + result.model : 'Illustrative fixture. No Jev API call was made.';
    $(kind + '-trace').textContent = JSON.stringify(result.inspection || {note: 'Illustrative fixture data, not a live Jev exchange.', request: result.input, answers: result.answers}, null, 2);
    if (kind === 'feedback') {
      renderSuggestions();
      document.querySelectorAll('#comments textarea').forEach(field => {
        const choice = result.choices[field.dataset.id];
        const impact = result.impacts[field.dataset.id];
        field.parentElement.append(node('p', 'Match: ' + choice.suggestion + ' · disruption ' + impact.score.toFixed(1) + '/3', 'note-result'));
      });
    } else {
      renderDecision();
      document.querySelectorAll('#evidence input').forEach(field => {
        const answer = result.answers['score_' + field.value];
        if (answer) field.nextElementSibling.append(node('p', 'Concern ' + answer.score.toFixed(1) + '/3', 'finding-score'));
      });
    }
    handoff();
  } catch (error) {
    if (version !== state[kind].version) return;
    $(kind + '-status').textContent = error.message;
    $(kind + '-status').className = 'status error';
  } finally {
    if (version === state[kind].version) {
      $('assess-' + kind).disabled = false;
    }
  }
}
async function start() {
  try {
    const response = await fetch('/api/config');
    if (!response.ok) throw new Error('Unable to load sample cases. Reload to retry.');
    config = await response.json();
    for (const [kind, collection] of [['product', config.products], ['release', config.releases]]) {
      Object.entries(collection).forEach(([id, item]) => {
        const option = node('option', item.name);
        option.value = id;
        $(kind).append(option);
      });
    }
    document.querySelectorAll('.key-note').forEach(el => { el.textContent = config.live_available ? 'Live Jev is available. API credentials stay on this server.' : 'No server API key. Fixtures work now; Live Jev will explain how to enable it.'; });
    $('product').addEventListener('change', loadProduct);
    $('release').addEventListener('change', loadRelease);
    $('reset-feedback').addEventListener('click', loadProduct);
    $('reset-release').addEventListener('click', loadRelease);
    $('add-comment').addEventListener('click', () => {
      if (comments().length >= 12) return;
      addNote('', 'c' + (comments().length + 1));
      clearResult('feedback', 'New note added. Enter at least three characters and assess with Live Jev.');
      $('comments').lastElementChild.querySelector('textarea').focus();
    });
    for (const kind of ['feedback', 'release']) {
      $(kind + '-mode').addEventListener('change', () => clearResult(kind, 'Mode changed. Assess again.'));
      $('assess-' + kind).addEventListener('click', () => assess(kind));
    }
    loadProduct();
    loadRelease();
    $('startup').hidden = true;
    $('workbench').hidden = false;
  } catch (error) { $('startup').textContent = error.message + ' Reload to retry.'; }
}
start();
