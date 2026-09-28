# Festival Control Room

Replay twenty minutes of synthetic volunteer reports at Northline Festival. Move crew starting positions or change staffing, then replay the same reports to compare the dispatch plan.

## Run locally

Python 3.10 or newer is required. No packages or build step are needed.

```sh
python3 demos/festival_control_room/festival_control_room.py serve
```

Open [Festival Control Room](http://127.0.0.1:8768). The initial plan uses labeled, hand-authored fixture judgments.

To enable Jev, set the key on the server before starting it.

```sh
read -rs 'TYPESAFE_API_KEY?TypeSafe API key: '; echo
export TYPESAFE_API_KEY
python3 demos/festival_control_room/festival_control_room.py serve
```

The key-entry command above is for zsh. In another shell, set `TYPESAFE_API_KEY` through your usual environment or secret manager. Select **Use live Jev** in the page. The server sends only the synthetic scenario to [TypeSafe's API](https://docs.typesafe.ai/api). The key stays on the server.

## Explore the dispatch plan

1. Play the event or scrub the timeline. Select a report to inspect the judgment and crew assignment.
2. Enable the initially off-duty Medical B to resolve the early medical queue, disable another crew, or drag a crew marker to a new starting position. Focus a crew marker and use the arrow keys for the keyboard equivalent.
3. Play again. The reports and judgments stay fixed while code recomputes availability, travel, and assignments.

Staffing edits reset and pause the replay. They change the starting layout for the whole simulation, not a crew's orders halfway through the event.

## How decisions work

Jev answers three independent questions for each report.

| Judgment | TypeSafe primitive | Code consumes it as |
| --- | --- | --- |
| Urgency | Score, from 0 to 3 | Priority among reports that have already arrived |
| Response team | Choice | Required crew specialty, or no match |
| Evidence for a safety escalation | Noul | Probability that the report supports supervisor escalation |

Code chooses the nearest idle crew with the required specialty. Busy crews remain reserved until their service period ends. Waiting reports compete by urgency when a crew becomes available. Crew IDs break ties. The browser renders the returned schedule and interpolates positions; it does not decide dispatch policy.

A Choice or Score confidence below 0.6 sends a report to review. Safety evidence at least 0.8 produces a simulated supervisor escalation. Evidence from 0.4 to below 0.8 asks for review. Lower evidence does not support escalation. These are illustrative thresholds, not evaluated operational policy. Safety escalation and crew dispatch are separate decisions.

A successful live evaluation is retained in memory for the server's lifetime. Staffing changes reuse those exact judgments without new inference. Restart the server to obtain a fresh evaluation. Failed API calls remain errors and never become fixture results labeled as Jev.

## Limits

This is a synthetic demonstration, not an emergency dispatch system. Travel uses straight-line distance at two map units per second with a ten-second minimum. Paths, obstacles, crowd density, actual walking speed, incident resolution, and service duration are not modeled from real observations. Moving reports stop at their dispatched rendezvous point.

The server binds to `127.0.0.1`. It has no user accounts, persistence, or public deployment configuration. Do not expose it as an authenticated public service without adding the appropriate hosting and access controls.

Live API behavior is implemented against the [HTTP reference](https://docs.typesafe.ai/api), [Score](https://docs.typesafe.ai/primitives/score), [Choice](https://docs.typesafe.ai/primitives/choice), and [Noul](https://docs.typesafe.ai/primitives/noul) documentation. [Composite scoring](https://docs.typesafe.ai/patterns/composite-scoring) informed retaining judgments independently of code policy. [Jevable](https://jevable.com/) was a reference for a public interactive demo. No live accuracy, cost, or latency claims are made.

## Verify

```sh
python3 -m unittest demos/festival_control_room/test_festival_control_room.py
node --check demos/festival_control_room/static/app.js
```

See [acceptance evidence](ACCEPTANCE.md) and the [design decision](DESIGN.md).
