# Launch Lab

Investigate three fictional releases in a synthetic release-readiness dashboard. Choose evidence, inspect each metric's test results and team notes, then reassess the launch claim. Friday Checkout has reassuring charts but failed required checks. Midnight Migration has a scary queue-lag chart with a documented cause and passing required checks. Profile Glow-Up has improving metrics but a flaky required mobile upload.

## Run

Python 3.10 or newer. No package installation or build step is needed.

```sh
python3 demos/launch_lab/launch_lab.py serve --port 8766
```

Open [Launch Lab](http://127.0.0.1:8766). The initial **Offline fixture** mode uses hand-authored, deterministic judgments. Its values demonstrate the interaction, not measured model accuracy. The countdown starts at the scenario's simulated time to launch when you open or switch releases.

For live Jev, set the key in the server's environment and restart it:

```sh
read -rs 'TYPESAFE_API_KEY?TypeSafe API key: '; echo
export TYPESAFE_API_KEY
python3 demos/launch_lab/launch_lab.py serve --port 8766
```

The first two lines use zsh; other shells can set the environment variable through their normal secret manager. Select **Live Jev** in the page and press **Ask Jev to reassess**. The browser sends only the release ID and chosen evidence IDs to the local server. The key stays on that server. Live failures show an error and never fall back to a fixture labeled as Jev.

## Try the evidence experiment

On Midnight Migration, assess with all six cards, then uncheck every card except the reassuring team note and reassess. Offline fixture claim support falls from 90% to 18%. Open **Inspect exact evidence and Jev answers** to see the state and typed answers. On Friday Checkout, the payment retry failure and missing rollback drill continue to block the release even when their cards are unchecked. The release checklist is the fixed rule registry; the selected cards are the evidence Jev receives.

Jev uses [Score](https://docs.typesafe.ai/primitives/score) for the concern in each included finding, [Choice](https://docs.typesafe.ai/primitives/choice) for the most useful next check, and [Noul](https://docs.typesafe.ai/primitives/noul) for whether selected evidence supports the release claim. Questions run together against one canonical state. Code handles fixed required-check blocks and the displayed readiness category. A Noul value at least 0.8 shows **Evidence supports shipping** only if all required checks pass. These are illustrative rules for a demo, not deployment policy.

The metrics, notes, tests, and judgments are fictional. The chart values are labeled synthetic and do not update from telemetry. There is no GitHub integration, deployment, account, or persistence. The local server binds to `127.0.0.1`.

## Verify

```sh
python3 -m unittest demos/launch_lab/test_launch_lab.py
node --check demos/launch_lab/static/app.js
```
