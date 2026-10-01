# Test every Jev Lab demo

Run these checks from the repository root. Python 3.11 or newer runs the whole collection. Node.js is needed only for JavaScript syntax checks. The demos themselves use Python's standard library and need no package installation.

## Prepare an offline run

1. Open a terminal in the repository root.
2. Run `export TYPESAFE_API_KEY=''` to keep all checks offline, even if your shell already has a key.
3. Start one demo with the command in its section below.
4. Open its local address. Keep the terminal running while you test.
5. Stop the server with Ctrl-C before testing the next demo. Some default ports overlap.

All scenarios and offline judgments are synthetic. A fixture response proves the interface works; it does not measure Jev accuracy. Each result inspector distinguishes the request, the actual response when available, and the application's decision rules. The [API contract](https://docs.typesafe.ai/api) specifies typed answers, not a written thinking trace. Any extra rationale actually returned remains in the JSON. The application never invents Jev's reasoning.

## Field match

Start `python3 demos/field_matchmaker/field_matchmaker.py serve` and open [Field match](http://127.0.0.1:8765).

1. Load **Clean headers** and select **Suggest mapping**. Expect the offline alias baseline.
2. Open the response inspector. Expect no live response and an explanation that Jev was not called.
3. Select **Lock mapping**. Expect a preview with distinct target fields.
4. Load **Two names** and suggest again. Assign both name columns to the company field. Expect a conflict and no valid import preview.
5. Edit the CSV. Expect the old mapping and response to clear before the next suggestion.
6. Enter rows with unequal column counts and suggest. Expect a validation error, not an old result.

Run `python3 -m unittest demos/field_matchmaker/test_field_matchmaker.py`.

## Claim check

Start `python3 demos/claim_check/claim_check.py serve` and open [Claim check](http://127.0.0.1:8766).

1. Load a sample. Expect editable claim and evidence, with no automatic API call.
2. Select **Run claim check**. Expect a keyword baseline and no Jev verdict while offline.
3. Open the response inspector. Expect an explanation that no Jev response is available. No request was sent.
4. Change the claim to a broader assertion. Expect the old assessment to clear.
5. Submit empty evidence. Expect required-field validation.
6. Repeat with the live setup below. Inspect the returned verdict, confidence, and full response beside the baseline.

Run `python3 -m unittest demos/claim_check/test_claim_check.py`.

## Interruption budget

Start `python3 demos/interruption_budget/interruption_budget.py serve` and open [Interruption budget](http://127.0.0.1:8767).

1. Select **Show sample inbox**. Expect Attention now, Review, and Digest lanes labeled as offline results.
2. Enter “The export failed and the team cannot finish today's handoff.” Select **Sort my event**.
3. Inspect the exchange. Offline mode has no model response.
4. Enable **Hold quiet hours** and sort again. Expect the code rule to hold eligible events without a Jev call.
5. Enable **Priority page flag** and sort. Expect the event in Attention now even during quiet hours, with no call for that event.
6. Edit the event or either rule. Expect old judgments and inspection to clear.

Run `python3 -m unittest demos/interruption_budget/test_interruption_budget.py`.

## Festival Control Room

Start `python3 demos/festival_control_room/festival_control_room.py serve` and open [Festival Control Room](http://127.0.0.1:8768).

1. Play the timeline. Expect reports and simulated crew movement.
2. Select a report. Inspect urgency, team choice, safety evidence, and the application assignment rule.
3. Inspect the exchange. The fixture plan must not claim a live response.
4. Enable Medical B. Expect the replay to reset and the dispatch schedule to change.
5. Focus a crew marker and use arrow keys. Expect the same starting-position edits supported by dragging.
6. With live setup, select **Use live Jev**. Capture the raw response, then change staffing. Expect the same cached exchange while code recalculates the schedule.

Run `python3 -m unittest demos/festival_control_room/test_festival_control_room.py`.

## Launch Lab

Start `python3 demos/launch_lab/launch_lab.py serve` and open [Launch Lab](http://127.0.0.1:8766).

1. Select Friday Checkout and reassess with the offline fixture. Expect blocked readiness from required failed or missing checks.
2. Exclude those evidence cards and reassess. Expect the required checks to continue blocking readiness.
3. Select Midnight Migration with all evidence. Reassess and expect 90% fixture support.
4. Keep only the reassuring team note. Reassess and expect 18% fixture support.
5. Open **Inspect exact evidence and Jev answers**. Check that only selected evidence enters the request and that the source is a fixture.
6. Change evidence or release. Expect the old assessment to clear. In live mode, inspect the complete returned envelope as well as typed answers.

Run `python3 -m unittest demos/launch_lab/test_launch_lab.py`.

## Feedback Kitchen

Start `python3 demos/feedback_kitchen/feedback_kitchen.py serve` and open [Feedback Kitchen](http://127.0.0.1:8767).

1. Choose Pantry & Co. Expect eight prepared comments, a fixed improvement catalog, and an illustrative baseline.
2. Select an improvement. Check its matching comments separately from support for its full claim.
3. Add improvements to the tray. Expect at most three, with removal available.
4. Edit a comment to “My saved list disappears whenever I lose mobile signal.” Expect every old judgment to clear.
5. Try a prepared baseline on edited text. Expect rejection; those labels apply only to the original comments.
6. With live setup, select **Assess with Jev**. Inspect the exact request and response, including Choice, Score, and Noul answers.
7. Edit while an assessment is pending. Expect the late response to remain discarded and the assessment control to become usable again.

Run `python3 -m unittest demos/feedback_kitchen/test_feedback_kitchen.py`.

## Jev Habitat

Start `python3 demos/jev_habitat/jev_habitat.py serve` and open [Jev Habitat](http://127.0.0.1:8777).

1. Choose a prepared room request and select **Evaluate request**. Expect a clearly labeled fixture result.
2. Open the inspector. Check state, questions, typed answers, and the separate application rule.
3. Raise the threshold to 1. Expect the proposal to be held without another API call.
4. Lower the threshold and select **Apply to room** when enabled. Expect only the browser simulation to change.
5. Reset the room or edit the request. Expect the proposal and old exchange to clear.
6. Enter text that is not a prepared request while offline. Expect an explicit fixture error, not an invented model answer.

Run `python3 -m unittest discover -s demos/jev_habitat -p 'test_*.py'`.

For its optional full browser check, keep the offline server on port 8777 and run `node demos/jev_habitat/browser-check.cjs` in an environment with Playwright and Chrome. These are verification tools, not demo dependencies.

## Repro Coach

1. Run the offline command below. Expect fixed follow-up questions for a vague report and inspection with no live response.

   ```sh
   python3 demos/repro_coach/repro_coach.py report 'Export is broken.'
   ```

2. Evaluate development fixtures and keep evidence outside the repository.

   ```sh
   python3 demos/repro_coach/repro_coach.py fixtures --split dev --evidence /tmp/repro-dev.jsonl
   ```

3. Read `/tmp/repro-dev.jsonl`. Expect offline provenance and per-report results. Do not describe the numbers as Jev accuracy.
4. With the key still empty, run the report command with `--live`. Expect unavailable status and no fabricated response.
5. With live setup, repeat the report with `--live`. Inspect the exact request and response alongside the fixed follow-up selection.

Run these checks:

```sh
python3 -m unittest demos/repro_coach/test_repro_coach.py
uvx ruff check demos/repro_coach
uvx mypy --check-untyped-defs demos/repro_coach/repro_coach.py
```

## Promise Catcher

1. Run a future commitment through the offline baseline.

   ```sh
   python3 demos/promise_catcher/promise_catcher.py catch \
     --source-id test-17 --author Ada \
     --sentence 'I will send the migration checklist tomorrow.'
   ```

2. Inspect the output. Expect offline provenance, the source ID, and no live Jev response. The baseline can propose a preview without writing one.
3. Repeat with “I sent the migration checklist yesterday.” Expect no new future-commitment preview.
4. Evaluate the development fixtures.

   ```sh
   python3 demos/promise_catcher/promise_catcher.py evaluate \
     --fixtures demos/promise_catcher/fixtures.jsonl \
     --split dev --evidence /tmp/promise-dev.jsonl
   ```

5. For persistence checks, use a new temporary preview file via `--preview /tmp/promise-test-previews.jsonl`. The saved preview includes the source sentence and leaves owner and due date for human confirmation. Repeating a source ID must not duplicate it. Changing its text or author must report a conflict.
6. With live setup, add `--live` to the catch command. Inspect both returned Noul answers and the full response. A live failure must not create an offline preview.

Run `python3 -m unittest demos/promise_catcher/test_promise_catcher.py`.

## Release Room

Start `python3 demos/release_room/release_room.py serve` and open [Release Room](http://127.0.0.1:8770).

1. Inspect the feedback and release sections. They use independently selected fictional examples; one does not prove facts about the other.
2. Assess the original feedback in prepared mode. Expect matched improvements, impact, and support labeled as fixture data.
3. Select an improvement for the shortlist. Expect a visible selection that does not alter release readiness.
4. Assess Friday Checkout. Expect HOLD because required checks fail or are missing.
5. Remove blocking evidence from the selected evidence and reassess. Expect HOLD to remain.
6. Switch to Midnight Migration and assess all evidence. Expect the supported release decision. Remove evidence and reassess to see support change.
7. Open each exchange inspector. Fixture data must be labeled; live mode shows the exact returned response. Application rules are distinct from model output.
8. Edit feedback. Expect only its assessment to clear. Change release evidence. Expect only the release assessment to clear.
9. Test without a key. Live mode must explain the missing key and preserve an error state.
10. Repeat on a narrow screen and with only a keyboard. All inputs, shortlist actions, evidence controls, and inspectors must remain reachable.

Run `python3 -m unittest discover -s demos/release_room -p 'test_*.py'`.

## Demo dashboard

Start `python3 demos/demo_dashboard/demo_dashboard.py serve` and open [Demo dashboard](http://127.0.0.1:8769).

1. Select each of the ten demos in the rail. Expect its purpose, run command, and request example.
2. Select a JSON helper. Expect the corresponding path to be highlighted.
3. Select **Release Room**. Expect `python3 demos/release_room/release_room.py serve` and the link to port 8770.
4. Start that server in another terminal and follow the link. Expect the combined workbench.
5. Reload the dashboard with `?demo=release_room`. Expect Release Room to remain selected.
6. Confirm that response values in the catalog are blank. The dashboard shows API shapes and never calls Jev itself.

Run `python3 -m unittest demos/demo_dashboard/test_demo_dashboard.py`.

## Run the entire automated suite

This runs each demo separately so modules with local imports resolve as documented. It also checks every static JavaScript file. A failure stops the run.

```sh
python3 - <<'PY'
from pathlib import Path
import subprocess
import sys

for folder in sorted(Path('demos').iterdir()):
    if folder.is_dir() and list(folder.glob('test_*.py')):
        print(f'Testing {folder}', flush=True)
        subprocess.run([sys.executable, '-m', 'unittest', 'discover',
                        '-s', str(folder), '-p', 'test_*.py'], check=True)
for script in sorted(Path('demos').glob('*/static/*.js')):
    subprocess.run(['node', '--check', str(script)], check=True)
PY
git diff --check
```

For the committed cross-demo browser check, run `node scripts/check-demo-browsers.cjs` with Playwright and Chrome available. It starts its own isolated offline servers, drives the pages at desktop and mobile widths, verifies stale-response and inspector behavior, and saves screenshots under `docs/screenshots/jev-response-studio/`. It never uses your API key.

## Check live Jev separately

1. Stop the offline server.
2. In zsh, enter your key without putting it in shell history, then export it.

   ```sh
   read -rs 'TYPESAFE_API_KEY?TypeSafe API key: '; echo
   export TYPESAFE_API_KEY
   ```

3. Restart the same server. Select live mode where a mode control exists.
4. Submit one synthetic example. Expect a real returned `model` and `answers` envelope. Check the inspector against the browser's local API response.
5. To verify Release Room against real API responses, run `node scripts/check-live-release-room.cjs http://127.0.0.1:8770` with Playwright and Chrome available. It makes two authenticated calls, checks that displayed exchanges match the server response, and saves labeled live screenshots.
6. Change an input while a call is pending. Expect the old response to stay cleared.
7. Stop the server and start it with `TYPESAFE_API_KEY=invalid-test-key`. Submit again. Expect an error or unavailable state and no fixture labeled as live.
8. Restore or clear the key when finished.

Live requests send the selected example to TypeSafe AI and may incur charges. Do not commit local evidence containing private inputs. An offline or mocked check does not verify authenticated service behavior, model accuracy, latency, or calibration.
