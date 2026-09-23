# Run Repro Coach

Repro Coach selects fixed follow-up questions for missing reproduction steps, an observed result, and an execution environment. The default fixture run evaluates the local keyword baseline. It does not call Jev.

Use Python 3.10 or later. The implementation was tested with Python 3.14.7. Reports are limited to 16,384 UTF-8 bytes. Live requests use a 30-second timeout and accept at most 1,000,000 response bytes.

```sh
python3 demos/repro_coach/repro_coach.py fixtures --split dev
python3 demos/repro_coach/repro_coach.py report "Export is broken."
```

The fixture command writes `evidence.jsonl`. Pass `--evidence PATH` to use another output. The committed fixture file contains 10 development reports and 20 held-out reports.

Each result has one status: `request_description`, `ready`, `review`, `unavailable`, or `not_run`. The `report` command accepts one report as its positional argument. The `fixtures` command accepts `--split dev` or `--split heldout`.

## Run the live experiment

Set the API key and opt in with `--live`. A live run sends the selected synthetic reports and questions to TypeSafe AI and may incur API charges.

```sh
TYPESAFE_API_KEY=... python3 demos/repro_coach/repro_coach.py fixtures \
  --split heldout --live --evidence /tmp/repro-heldout.jsonl
```

The script makes one request per report with a 30-second timeout. It does not retry. Failed or invalid responses count as unavailable. Do not use baseline-only evidence to claim Jev accuracy.

If `--live` is set without `TYPESAFE_API_KEY`, the result is `unavailable` with `unattempted` provenance. No request is made. A completed request has `live_jev` provenance, including failed responses.

## Verify the implementation

```sh
python3 -m unittest demos/repro_coach/test_repro_coach.py
uvx mypy --check-untyped-defs demos/repro_coach/repro_coach.py
uvx ruff check demos/repro_coach
```

No live run has been made because this implementation session had no API key. The policy tests verify local routing and boundary handling only.
