# Launch Lab and Feedback Kitchen acceptance

These medium-sized demos implement the release-readiness and feedback-evidence brief. Both stay local and use Python's standard library with static HTML, CSS, and JavaScript. They introduce no database, deployments, or GitHub integration.

## Behavior

Launch Lab has three releases, six evidence cards per release, three inspectable metric charts, a simulated countdown, and a release checklist. One assessment batches Score for each selected finding, Choice for the next check, and Noul for claim support. Required failed, flaky, or missing tests block readiness even when their evidence is unchecked. Selecting another release or changing evidence clears the old assessment.

Feedback Kitchen has three products, eight prepared comments each, three catalog improvements per product, and unclear/no-match outcomes. Visitors can rewrite a comment, add up to four comments, inspect exact inputs and responses, and collect improvements in a tray. Live assessment batches matching, impact, and support judgments. Noul considers the entire comment collection. The displayed matched comments are the Choice selections, not a generated explanation from Jev.

The prepared fixtures demonstrate the interactions without an API key. Their numbers are illustrative. Edited Kitchen comments require a live assessment rather than reusing labels assigned to the original text. API failures remain errors and never silently become model-labeled fixtures.

## Verification

On 2026-09-28, all 87 Python tests passed across eight demo suites, including 10 new tests. The two new suites cover catalog shape, release blockers, exact selected evidence, edited-fixture rejection, live response parsing, HTTP status recovery, and local request validation. JavaScript syntax checks and `git diff --check` passed.

Browser checks in Chromium exercised all six scenarios, chart drawer and Escape, evidence removal and reassessment, comment-to-suggestion navigation, edit/add invalidation, tray add/remove, and product changes. Screenshots were captured at 1440px desktop and 390px mobile. The final checked pages have no horizontal document overflow or JavaScript page errors. A first-round mobile overflow and inline match-label defect in Kitchen were fixed before recapture.

A delayed-response browser check confirmed that editing while a request is in flight leaves the assessment button usable and cannot restore stale judgments. Keyboard checks confirmed release-tab focus and tray add/remove focus. The editor preserves unsaved text when selecting a suggestion. Unclear/no-match comments and missing-key errors show their own states.

Independent Sol high reviews covered standards, the feature brief, and the four screenshots. The spec and visual verdict was **ship**. Standards fixes addressed request validation, stale state, recovery messages, and tray focus. The remaining style note is that some JavaScript render templates are dense; it does not affect the verified behavior.

Screenshots:

- [Launch desktop](../demos/launch_lab/screenshots/desktop.png) and [mobile](../demos/launch_lab/screenshots/mobile.png).
- [Kitchen desktop](../demos/feedback_kitchen/screenshots/desktop.png) and [mobile](../demos/feedback_kitchen/screenshots/mobile.png).

Run the Python suites from the repository root:

```sh
python3 - <<'PY'
import pathlib
import subprocess
import sys
for folder in sorted(pathlib.Path('demos').iterdir()):
    if list(folder.glob('test_*.py')):
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(folder), '-p', 'test_*.py'], check=True)
PY
node --check demos/launch_lab/static/app.js
node --check demos/feedback_kitchen/static/app.js
```

## Limits

No `TYPESAFE_API_KEY` was present during implementation. Tests verified the request/response integration using controlled transport responses and HTTP errors. Real authenticated Jev behavior, latency, cost, and calibration remain unmeasured. The support thresholds are demonstration rules, not validated release or product policy. Google Fonts are optional presentation requests; local system fallbacks keep both demos usable when font requests fail.

The server ports default to 8766 and 8767. See the [Launch run guide](../demos/launch_lab/README.md) and [Kitchen run guide](../demos/feedback_kitchen/README.md) for API setup. This document records the feature scope and acceptance in place of a separate roadmap issue.
