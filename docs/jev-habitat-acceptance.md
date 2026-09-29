# Jev Habitat acceptance

## Requested behavior

Build an independent, interactive UI that explains Jev's API workflow. The user selected a playful room simulation with an API inspector. Include a simple guide to every UI demo, review the work, create a PR, and merge it.

## Design decision

Use a stateless Python evaluator and browser-owned simulated room state. A separate Sol high design reviewer compared this with server-owned sessions. The stateless design needs no session storage or locks and keeps each demo independent. An input revision prevents delayed answers from becoming current after an edit or reset.

Jev receives one state snapshot and three independent questions. Choice selects a supported action. Score describes requested lighting brightness and matters only for a lighting action. Noul estimates whether the request describes an applicable change. Application code owns thresholds, brightness rounding, and simulated device updates. Changing a threshold reuses the answer and does not call Jev.

The offline path accepts only prepared examples with their original room state. Fixtures are illustrative and make no claim about Jev accuracy. The live path keeps credentials on the local server and never substitutes a fixture after failure. No real device, database, schema, deployment, or existing demo is changed.

## Verification

All 93 Python tests across the nine demo directories passed. Habitat's six tests cover fixture eligibility, request validation, malformed answers, missing credentials, provider failures, unused speculative brightness answers, and an uncertain fixture that changes the room. JavaScript syntax, Python compilation, and `git diff --check` passed.

The committed `demos/jev_habitat/browser-check.cjs` exercises a running local server. The desktop and mobile pass verified all three device changes, no-change handling, JSON inspection, local threshold changes without extra requests, edited-fixture rejection, missing-key errors, stale-response discard, reduced motion, and no page errors or horizontal overflow. Run it with Playwright and Chrome available after starting Habitat on port 8777.

Screenshots in `demos/jev_habitat/screenshots/` are browser captures of the illustrative fixture mode at desktop width 1440 and mobile width 390. They are not generated artwork or live Jev results.

The single Impeccable detector pass found small functional text, one low-contrast label, external display fonts, and cramped-header advisories. The implementation increased labels to at least 12px, darkened plan text, used system fonts, and padded headers. The plan grid remains because it belongs to the room diagram. A visual pass also moved room labels clear of furniture and replaced hard shadows. The independent Sol high correctness review found that the uncertain lighting fixture targeted the starting brightness. Commit `7a74970` changes its target from 2 to 3 and adds a regression check. The reviewer independently verified that lowering the threshold from .70 to .50 makes Apply available without another request and that Apply changes the lights from 2 to 3. The full branch whitespace check also passes after removing a trailing blank line. The reviewer passed the correction with no new actionable findings. The separate Sol high specification and UI reviewer returned `ship` after inspecting desktop and mobile captures, the source, the direction contract, and the guide. No material UI or guide blocker remained in that review.

## Limits

No `TYPESAFE_API_KEY` was available in the task environment. Real Jev inference quality, latency, and cost remain unmeasured. Controlled responses can verify request handling and application behavior but cannot establish model accuracy. All thresholds and room controls are demonstration policy.
