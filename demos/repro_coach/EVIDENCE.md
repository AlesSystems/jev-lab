# Repro Coach evidence

The offline checks cover threshold endpoints, review routing, invalid Noul values, empty automatic checklists, response shape validation, evaluation denominators, blank reports, and baseline-only provenance.

Evidence distinguishes `baseline_only`, `unattempted`, and `live_jev` provenance. An attempted request without valid input-token usage counts as missing usage.

The committed [offline baseline evidence](evidence/offline-baseline.jsonl) records 20 held-out synthetic reports. The keyword baseline matched 11 of 20 whole checklists. The fixture labels are author-supplied and await independent human validation, so this count is an implementation observation rather than a quality claim.

Reproduce the file with Python 3.10 or later:

```sh
python3 demos/repro_coach/repro_coach.py fixtures \
  --split heldout \
  --evidence demos/repro_coach/evidence/offline-baseline.jsonl
```

The implementation was tested with Python 3.14.7. No live Jev evidence exists. After a live held-out run, record the evidence file, question hash, requested and returned model, counts, failures, latency, usage, baseline comparison, and one decision: `keep`, `revise`, or `use the baseline`.
