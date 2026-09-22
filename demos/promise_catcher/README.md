# Follow-up Promise Catcher

This local demo checks one selected sentence for an explicit future commitment by its known author. It proposes a task preview only when the commitment is clear and the action is not complete. The preview preserves the source sentence and leaves both the owner and the due date for human confirmation.

The default mode runs a phrase baseline. It does not call Jev. Pass `--live` to call `jev-1.13.0` through `https://api.typesafe.ai/v1/systemone` with `TYPESAFE_API_KEY`.

## Check one sentence

Run the baseline without writing a preview.

```sh
python3 demos/promise_catcher/promise_catcher.py catch \
  --source-id note-17 \
  --author Ada \
  --sentence 'I will send the migration checklist tomorrow.'
```

Add `--preview previews.jsonl` to opt in to a local task preview. The preview records `engine: offline_baseline`. Add `--live` to use Jev; a live failure never falls back to a baseline preview.

## Evaluate the fixtures

Run the offline baseline on all 30 synthetic fixtures.

```sh
python3 demos/promise_catcher/promise_catcher.py evaluate \
  --fixtures demos/promise_catcher/fixtures.jsonl \
  --evidence evidence.jsonl
```

Use `--split dev` while changing questions. Freeze the question and threshold settings before you run `--split heldout --live`. The live command sends the synthetic author and sentence to TypeSafe AI and may incur API charges.

The fixtures contain 10 development cases and 20 held-out cases. The held-out set has 10 labeled commitments and 10 labeled non-commitments. These are synthetic author labels pending independent human validation. Offline evidence proves baseline behavior, routing, and provenance. It does not measure Jev accuracy.

## Limits

The preview store supports one writer at a time. It uses atomic file replacement and persistent source-ID deduplication. A repeated ID with changed text or author becomes a conflict. Use file locking or SQLite only if concurrent writers become necessary.

The demo does not calculate relative dates, confirm ownership, schedule work, or connect to a calendar or task tracker.
