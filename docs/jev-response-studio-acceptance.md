# Jev response inspection and Release Room acceptance

Verified on 2026-10-01. The scope follows the request to expose Jev responses, add a larger release and feedback demo to the dashboard, and document step-by-step checks for all demos. The task started from `b3cd867`, the existing dashboard branch. The original checkout's uncommitted API-key setup work remains untouched in a separate checkout.

## Delivered behavior

Seven browser demos now expose or clarify their exact Jev exchanges. Claim Check, Field Match, Interruption Budget, and Festival previously discarded the response after parsing it. Launch Lab now retains the complete envelope. Feedback Kitchen and Habitat keep their existing inspectors with explicit provenance. Both CLI demos add inspection to their JSON results and fixture evidence.

Returned JSON remains distinct from application rules. Jev's documented API returns typed judgments, not a written thinking trace. Any returned extra rationale fields remain visible. No local prose pretends to be model reasoning. Offline baselines have no real response; prepared answers are explicitly fixtures. The dashboard continues to show blank API shapes.

Release Room combines the existing feedback and release engines, with independent assessments and a local improvement shortlist. Required release checks still block readiness when evidence is deselected. Editing one desk invalidates only its own result. The new page uses a separate editorial design and a self-hosted Newsreader font under the included OFL license. It does not deploy or persist a plan.

## Reproducible verification

- All 111 Python tests passed across 11 demo suites using the runner in the [developer testing guide](testing-demos.md#run-the-entire-automated-suite).
- All nine static JavaScript files passed `node --check`. Both browser-check scripts passed syntax checks. `git diff --check` passed.
- Ruff passed for Release Room, Repro Coach, and Promise Catcher. Mypy passed for both CLI implementations.
- Existing browser suites have 32 pre-existing Ruff findings, with zero new findings in the comparison. Dashboard has an existing `EXE001` shebang/file-mode finding. These are not reported as a clean repository-wide lint pass.
- The [offline browser check](../scripts/check-demo-browsers.cjs) exercised all nine pages independently at 1440×1000 and 390×844, with no page errors or horizontal overflow. It covers inspectors, input invalidation, code-rule precedence, Release Room HOLD/READY/REVIEW, missing keys, edited-fixture rejection, independent results, and a delayed stale response. See [browser results](screenshots/jev-response-studio/browser-results.json).
- An authenticated Claim Check call returned `jev-1.13.0`. The [live Release Room check](../scripts/check-live-release-room.cjs) verified that rendered inspection JSON exactly matched both local API responses. Feedback returned 19 answers and release returned 8. Friday Checkout remained HOLD. See [live results](screenshots/jev-response-studio/live-results.json).
- Independent standards and spec reviewers found incorrect manual expectations and a mobile-check gap. Both were corrected. The reviewers used the same model family. Authenticated checks were performed by the parent, not independently repeated by the reviewers.

The Impeccable detector reported inherited design-system mismatches and older-page warnings. The new page's small text was increased before the final desktop/mobile confirmation. The existing Field Match hover contrast warning remains outside this response-inspector change. Existing pages retain their visual identities.

## Verified attachments

Each offline screenshot comes from an exercised page with its inspector open. Live screenshots are separately labeled. The [decision record](jev-response-studio-decisions.tsv) links the checks that support the main choices.

| Demo | Desktop | Mobile |
| --- | --- | --- |
| Release Room | [Fixture](screenshots/jev-response-studio/release_room-desktop.png) | [Fixture](screenshots/jev-response-studio/release_room-mobile.png) |
| Claim Check | [Offline](screenshots/jev-response-studio/claim_check-desktop.png) | [Offline](screenshots/jev-response-studio/claim_check-mobile.png) |
| Field Match | [Offline](screenshots/jev-response-studio/field_matchmaker-desktop.png) | [Offline](screenshots/jev-response-studio/field_matchmaker-mobile.png) |
| Interruption Budget | [Code rule](screenshots/jev-response-studio/interruption_budget-desktop.png) | [Code rule](screenshots/jev-response-studio/interruption_budget-mobile.png) |
| Festival | [Fixture](screenshots/jev-response-studio/festival_control_room-desktop.png) | [Fixture](screenshots/jev-response-studio/festival_control_room-mobile.png) |
| Launch Lab | [Fixture](screenshots/jev-response-studio/launch_lab-desktop.png) | [Fixture](screenshots/jev-response-studio/launch_lab-mobile.png) |
| Feedback Kitchen | [Fixture](screenshots/jev-response-studio/feedback_kitchen-desktop.png) | [Fixture](screenshots/jev-response-studio/feedback_kitchen-mobile.png) |
| Habitat | [Fixture](screenshots/jev-response-studio/jev_habitat-desktop.png) | [Fixture](screenshots/jev-response-studio/jev_habitat-mobile.png) |
| Dashboard | [Catalog](screenshots/jev-response-studio/demo_dashboard-desktop.png) | [Catalog](screenshots/jev-response-studio/demo_dashboard-mobile.png) |

[Authenticated Release Room](screenshots/jev-response-studio/release_room-live-desktop.png) and [actual returned response detail](screenshots/jev-response-studio/release_room-live-response.png) show the two live assessments.

## Limits and impacts

The live checks verify successful calls and response rendering, not accuracy, calibration, latency, or cost claims. The remaining demos' new inspection paths use deterministic mocked transports and offline browser checks. Error bodies that cannot be decoded or exceed limits are not retained as JSON. Inspectors and CLI evidence can contain submitted text; use synthetic inputs for shared evidence.

The new local server uses loopback, bounded JSON, same-origin checks, and existing validators. Keys stay in the server environment. No database schema, authentication system, deployment, or external notifications are added. Default ports remain unchanged; Release Room uses 8770. Test each shared-port demo sequentially or choose another port.
