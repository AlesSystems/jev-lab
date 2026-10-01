# Release Room

A release and feedback command center with two independent synthetic sample desks. Edit customer notes, assess their improvement claims, choose a shortlist, then inspect a release's evidence and required checks. The products and releases are unrelated samples. Feedback popularity never changes release blockers.

The server imports the existing Feedback Kitchen and Launch Lab engines and catalogs. It does not introduce a second release policy. HOLD means a required check failed, is missing, or is flaky. READY requires all required checks to pass and at least 80% evidence support. Otherwise the decision is REVIEW. These are illustrative demo rules, not deployment policy.

## Run

```sh
python3 demos/release_room/release_room.py serve --port 8770
```

Open <http://127.0.0.1:8770>. Fixtures need no API key. The server automatically loads `TYPESAFE_API_KEY` from the repository root `.env` file. To use live assessments, set the key there or in the server environment and restart the server. Both desks default to fixtures; select **Live Jev** separately for each desk, then click its **Assess** button. Credentials remain on the loopback server. Live failures stay errors and never become fixture successes. Each desk has its own mode, result, pending state, and exchange inspection.

## Test the workbench

1. Start the server and open the page. Both decisions begin unassessed.
2. Press **Assess feedback** with the original Pantry & Co. notes. Confirm the source says illustrative fixture, each note shows a match and disruption score, and improvement claims show corpus support.
3. Select **Offline shopping lists**. Confirm the working handoff names it but the release remains UNREAD.
4. Edit a note. Confirm feedback judgments disappear immediately and the release is unaffected. Assess in fixture mode. Confirm the explicit rejection asks for Live Jev or reset; no fixture is invented for edited text.
5. Press **Reset notes**. Select another sample product and confirm the shortlist clears. Add a note, enter at least three characters, and use Live Jev when configured.
6. Assess **Friday Checkout**. Confirm HOLD with two required blockers. Uncheck every evidence item, assess again, and confirm the blockers remain.
7. Select **Midnight Migration**, leave all evidence selected, and assess the fixture. Confirm READY with 90% support. Uncheck everything except **Team note**, reassess, and confirm REVIEW with 18% support.
8. Inspect both exchange disclosures. Fixtures explicitly say no Jev call occurred. With Live Jev enabled, confirm exact requests and complete returned responses are visible. Any API-provided reasoning fields remain in that response; the demo does not fabricate hidden thinking.
9. With no key configured, switch one desk to Live Jev and assess. Confirm a key error, no result, and no impact on the other desk's result.
10. During a live request, change a note, mode, product, release, or evidence selection. Confirm the old response never repopulates a stale result. Reassess the current input.
11. Use Tab, Shift+Tab, Space, and Enter to operate controls and disclosures. Resize to a 390px viewport. Confirm stacked desks, readable proof, and no horizontal page overflow.

```sh
python3 -m unittest demos/release_room/test_release_room.py
node --check demos/release_room/static/app.js
```

No persistence, deployment, account system, or production telemetry is included. Reloading clears the workspace. Live calls are only sent when an assessment button is pressed in Live Jev mode. See the [verified screenshots and acceptance record](../../docs/jev-response-studio-acceptance.md) and [all-demo testing guide](../../docs/testing-demos.md).
