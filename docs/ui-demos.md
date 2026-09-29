# Run the UI demos

These six local pages use Python's standard library and a browser. Use Python 3.10 or newer and run commands from the repository root. No package install or build step is needed. Each server binds to `127.0.0.1`; stop it with Ctrl-C.

Start a page with its command below, then open the listed address. To use live Jev, set `TYPESAFE_API_KEY` in the same server environment before starting the command. For example, in zsh:

```sh
read -rs 'TYPESAFE_API_KEY?TypeSafe API key: '; echo
export TYPESAFE_API_KEY
```

The key stays on the local server. Without it, the pages show their stated offline baselines or fixtures. Those results are examples, not measured Jev accuracy. A failed live call stays an error or unavailable result; it is not silently presented as a Jev judgment.

| Page | Start command | Open |
| --- | --- | --- |
| [Field match](../demos/field_matchmaker/README.md) | `python3 demos/field_matchmaker/field_matchmaker.py serve` | http://127.0.0.1:8765 |
| [Claim check](../demos/claim_check/README.md) | `python3 demos/claim_check/claim_check.py serve` | http://127.0.0.1:8766 |
| [Interruption budget](../demos/interruption_budget/README.md) | `python3 demos/interruption_budget/interruption_budget.py serve` | http://127.0.0.1:8767 |
| [Festival Control Room](../demos/festival_control_room/README.md) | `python3 demos/festival_control_room/festival_control_room.py serve` | http://127.0.0.1:8768 |
| [Launch Lab](../demos/launch_lab/README.md) | `python3 demos/launch_lab/launch_lab.py serve` | http://127.0.0.1:8766 |
| [Feedback Kitchen](../demos/feedback_kitchen/README.md) | `python3 demos/feedback_kitchen/feedback_kitchen.py serve` | http://127.0.0.1:8767 |

Claim check and Launch Lab share port 8766. Interruption budget and Feedback Kitchen share port 8767. To run either pair together, add `--port 8770` to one start command and open that port in the browser. Every server accepts `--port`.

## Field match

Load a sample or paste a CSV, then select **Suggest mapping**. The alias lookup is the code baseline for five accepted fields. With a key, Jev chooses a target field or `unmapped` for each column from its header and first three rows. Review the selects and select **Lock mapping** to validate a preview. Code rejects duplicate targets; this page does not import the CSV. Custom CSVs have no fixture labels.

## Claim check

Load an example, edit the claim or evidence, then select **Run claim check**. Keyword overlap is the code baseline. With a key, Jev chooses `supported`, `contradicted`, or `insufficient_evidence`. Code sends low confidence to review. Without a key, custom checks show only the baseline and no fixture verdict.

## Interruption budget

Enter an event and select **Sort my event**, or select **Show sample inbox**. The event-type lookup is the offline baseline for Attention now, Review, and Digest. With a key, Jev scores eligible events. Toggle **Hold quiet hours** or **Priority page flag** to see code rules take precedence. Quiet hours skip Jev; the page flag always remains in Attention now. The page sends no notification.

## Festival Control Room

Play or scrub the synthetic twenty-minute event. Select a report, move a crew marker, or change staffing and replay to compare assignments. The starting plan uses hand-authored fixture judgments. With a key, select **Use live Jev** to obtain Score urgency, Choice response team, and Noul safety evidence judgments. Code schedules the nearest available crew of the required specialty and handles queues. Staffing changes reuse the same judgments in that server process while code recomputes the schedule. The escalation is simulated.

## Launch Lab

Choose a fictional release, inspect its signals, select evidence cards, and press **Ask Jev to reassess**. **Offline fixture** uses hand-authored answers. With a key, select **Live Jev** for Score concern, Choice next check, and Noul support for the launch claim. Code keeps required checks in force even when you exclude their evidence cards. Try Midnight Migration with all cards, then only its reassuring team note; the offline support changes from 90% to 18%.

## Feedback Kitchen

Choose a fictional product, inspect feedback, and collect up to three improvements. The initial eight comments have a prepared illustrative baseline. Edit or add a comment to clear the old judgments, then select **Assess with Jev**. With a key, Jev uses Choice to match comments to a fixed improvement catalog, Score for disruption, and Noul for support across the whole comment collection. Code limits the catalog and tray. The prepared baseline covers only unedited examples, so changed feedback needs a live assessment.

## Command-line demos

[Repro Coach](../demos/repro_coach/README.md) and [Promise Catcher](../demos/promise_catcher/README.md) run from the command line and have no local page. Their READMEs contain commands and environment requirements.
