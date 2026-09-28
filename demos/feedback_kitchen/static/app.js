const $ = (id) => document.getElementById(id);
let products = {}, productId = 'recipe', comments = [], result = null, selectedComment = null, selectedSuggestion = null, tray = [], revision = 0, pending = null, nextCommentId = 1, editorCommentId = null;
const labelFor = (id) => products[productId].suggestions.find(s => s.id === id)?.name ?? (id === 'unclear' ? 'Unclear' : id === 'no_match' ? 'No match' : 'Awaiting assessment');
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function setStatus(text) { $('status').textContent = text; }
function invalidate() { revision++; pending?.abort(); pending = null; $('assess').disabled = false; $('assess').innerHTML = 'Assess with Jev <span aria-hidden="true">↗</span>'; result = null; tray = []; $('source-pill').textContent = 'Needs reassessment'; setStatus('Feedback changed. Use Assess with Jev for fresh judgments.'); render(); }
function selectProduct(id) { if (!products[id]) return; revision++; pending?.abort(); pending = null; $('assess').disabled = false; $('assess').innerHTML = 'Assess with Jev <span aria-hidden="true">↗</span>'; productId = id; comments = products[id].comments.map((text,i) => ({id:`c${i+1}`,text})); result = null; selectedComment = 'c1'; selectedSuggestion = products[id].suggestions[0].id; tray = []; editorCommentId = null; $('source-pill').textContent = 'Prepared baseline'; setStatus(''); render(); assess('baseline'); }
function render() {
  const draft = editorCommentId === selectedComment ? $('edit-comment').value : null;
  const active = document.activeElement?.dataset;
  const restore = active ? Object.entries(active).find(([key]) => ['comment','suggestion','product','remove'].includes(key)) : null;
  const product = products[productId];
  $('products').innerHTML = Object.entries(products).map(([id,p]) => `<button type="button" data-product="${id}" aria-pressed="${id===productId}">${escapeHtml(p.name)}</button>`).join('');
  $('product-description').textContent = product.description;
  $('comment-count').textContent = `${comments.length} notes`;
  $('comments').innerHTML = comments.map((c,i) => `<button class="comment-card" type="button" data-comment="${escapeHtml(c.id)}" aria-pressed="${selectedComment===c.id}"><span class="card-top"><span>Voice ${String(i+1).padStart(2,'0')}</span><span>${result ? `Impact ${Number(result.impacts[c.id]?.score ?? 0).toFixed(1)}/3` : 'Unassessed'}</span></span><span>${escapeHtml(c.text)}</span><span class="card-match">${result ? escapeHtml(labelFor(result.choices[c.id]?.suggestion)) : 'Needs assessment'}</span></button>`).join('');
  $('suggestions').innerHTML = product.suggestions.map(s => {const support = result?.supports[s.id]; return `<button type="button" class="suggestion-card" data-suggestion="${s.id}" aria-pressed="${selectedSuggestion===s.id}"><span class="name">${escapeHtml(s.name)}</span><span class="description">${escapeHtml(s.claim)}</span><span class="support">${support == null ? 'Evidence pending' : `${Math.round(support*100)}% claim support · ${comments.filter(c=>result.choices[c.id]?.suggestion===s.id).length} matched notes`}</span></button>`}).join('');
  const selected = comments.find(c=>c.id===selectedComment);
  $('edit-comment').disabled = !selected;
  $('save-edit').disabled = !selected;
  $('edit-comment').value = draft ?? selected?.text ?? '';
  editorCommentId = selectedComment;
  renderEvidence();
  $('tray-items').innerHTML = tray.length ? tray.map(id => `<button type="button" data-remove="${id}" aria-label="Remove ${escapeHtml(labelFor(id))}">${escapeHtml(labelFor(id))} ×</button>`).join('') : '<span class="evidence-empty">Your picks will appear here.</span>';
  $('inspection').textContent = result ? JSON.stringify(result.inspection, null, 2) : 'Reassess to inspect this version of the feedback.';
  if (restore) document.querySelector(`[data-${restore[0]}="${CSS.escape(restore[1])}"]`)?.focus();
}
function renderEvidence() {
  const suggestion = products[productId].suggestions.find(s=>s.id===selectedSuggestion);
  if (!suggestion) { $('evidence-body').innerHTML = `<div class="evidence-summary"><strong>${selectedSuggestion === 'unclear' ? 'The request is unclear' : 'No catalog match'}</strong><p>${selectedSuggestion === 'unclear' ? 'The comment describes a problem without pointing to a specific improvement.' : 'This comment does not match the prepared improvement catalog.'}</p></div><p class="evidence-empty">Ask for more detail or examine another voice before selecting an improvement.</p>`; return; }
  const score = result?.supports[suggestion.id], matches = result ? comments.filter(c => result.choices[c.id]?.suggestion===suggestion.id) : [];
  const verdict = score == null ? 'Waiting for assessment' : score >= .75 ? 'Supported by these notes' : score >= .4 ? 'Promising, check the cause' : 'Not yet supported';
  $('evidence-body').innerHTML = `<div class="evidence-summary"><strong>${escapeHtml(verdict)}</strong><p>${escapeHtml(suggestion.claim)}</p>${score == null ? '' : `<div class="support-meter" role="meter" aria-label="Claim support" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(score*100)}"><span style="width:${Math.round(score*100)}%"></span></div><p style="margin-top:9px;font-size:12px">${Math.round(score*100)}% support · ${escapeHtml(result.source)}</p><p style="margin-top:8px;font-size:12px">Claim support considers all ${comments.length} comments. Matching comments are shown below.</p>`}</div><div class="evidence-list">${matches.length ? matches.map(c=>`<div class="evidence-item"><small>Voice ${comments.indexOf(c)+1} · impact ${Number(result.impacts[c.id]?.score ?? 0).toFixed(1)}/3</small><p>“${escapeHtml(c.text)}”</p></div>`).join('') : `<p class="evidence-empty">${result ? 'No comments matched this improvement. The claim may still need a better explanation or fresh feedback.' : 'Run an assessment to see which comments connect to this idea.'}</p>`}</div><button id="choose-suggestion" class="primary" type="button" style="margin-top:20px" ${tray.includes(suggestion.id)?'disabled':''}>${tray.includes(suggestion.id)?'Added to tray':'Choose this improvement'}</button>`;
  $('choose-suggestion').addEventListener('click', () => { if (tray.length >= 3) {setStatus('Your tray is full. Remove a choice to add another.'); return;} tray.push(suggestion.id); render(); document.querySelector(`[data-remove="${suggestion.id}"]`)?.focus(); });
}
async function assess(mode='live') {
  const at = revision, controller = new AbortController(); pending?.abort(); pending = controller;
  $('assess').disabled = true; $('assess').textContent = 'Assessing…'; setStatus(mode === 'live' ? 'Jev is reading these comments…' : 'Loading prepared baseline…');
  try {
    const response = await fetch('/api/assess', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:productId,comments,mode}),signal:controller.signal});
    const data = await response.json();
    if (at !== revision || pending !== controller) return;
    if (!response.ok) throw new Error(data.error || 'Assessment failed.');
    result = data; $('source-pill').textContent = data.source; setStatus(mode==='live' ? 'Fresh Jev assessment ready. Select a card to inspect its evidence.' : 'Illustrative prepared baseline. Edit a comment to try a live reassessment.'); render();
  } catch (error) { if (error.name !== 'AbortError' && at === revision && pending === controller) {result = null; $('source-pill').textContent = 'Assessment unavailable'; setStatus(error.message); render();} }
  finally { if (pending === controller) {pending = null; $('assess').disabled = false; $('assess').innerHTML = 'Assess with Jev <span aria-hidden="true">↗</span>';} }
}
$('products').addEventListener('click', e => {const button=e.target.closest('[data-product]'); if(button) selectProduct(button.dataset.product)});
$('comments').addEventListener('click', e => {
  const button = e.target.closest('[data-comment]');
  if (!button) return;
  selectedComment = button.dataset.comment;
  const match = result?.choices[selectedComment]?.suggestion;
  if (match) selectedSuggestion = match;
  render();
});
$('suggestions').addEventListener('click', e => {
  const button = e.target.closest('[data-suggestion]');
  if (!button) return;
  selectedSuggestion = button.dataset.suggestion;
  render();
});
$('tray-items').addEventListener('click', e => {
  const button = e.target.closest('[data-remove]');
  if (!button) return;
  tray = tray.filter(id => id !== button.dataset.remove);
  render();
  ($('tray-items').querySelector('button') ?? $('tray-heading')).focus();
});
$('assess').addEventListener('click',()=>assess('live'));
$('save-edit').addEventListener('click',()=>{const value=$('edit-comment').value.trim(); if(value.length<3){setStatus('Write at least 3 characters before saving.');return;} const comment=comments.find(c=>c.id===selectedComment); if(!comment || comment.text===value)return; comment.text=value; invalidate();});
$('add-form').addEventListener('submit',e=>{e.preventDefault();const value=$('new-comment').value.trim();if(value.length<3){setStatus('Write at least 3 characters to add feedback.');return;}if(comments.length>=12){setStatus('This demo holds up to 12 comments. Edit an existing card instead.');return;}const id=`u${nextCommentId++}`;comments.push({id,text:value});selectedComment=id;$('new-comment').value='';invalidate();});
fetch('/api/config').then(r=>{if(!r.ok)throw new Error('Could not load products.');return r.json()}).then(data=>{products=data.products;selectProduct('recipe')}).catch(error=>setStatus(error.message));
