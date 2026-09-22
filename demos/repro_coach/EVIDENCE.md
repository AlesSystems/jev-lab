# Repro Coach evidence

The offline checks cover threshold endpoints, review routing, invalid Noul values, empty automatic checklists, response shape validation, evaluation denominators, blank reports, and baseline-only provenance.

Evidence distinguishes `baseline_only`, `unattempted`, and `live_jev` provenance. An attempted request without valid input-token usage counts as missing usage.

The committed [offline baseline evidence](evidence/offline-baseline.jsonl) records 20 held-out synthetic reports. The keyword baseline matched 3 of 20 whole checklists. The replacement set removed overlap with development templates before any live run and passed an independent fixture review. The synthetic labels still await human validation, so this count is an implementation observation rather than a quality claim.

The fixture SHA-256 recorded by the run is `bd13207d032859cb2a3100d3208329803c5268e15206033c7be079f7167fd71c`.

Reproduce the file with Python 3.10 or later:

```sh
python3 demos/repro_coach/repro_coach.py fixtures \
  --split heldout \
  --evidence demos/repro_coach/evidence/offline-baseline.jsonl
```

The implementation was tested with Python 3.14.7. No live Jev evidence exists. After a live held-out run, record the evidence file, question hash, requested and returned model, counts, failures, latency, usage, baseline comparison, and one decision: `keep`, `revise`, or `use the baseline`.
