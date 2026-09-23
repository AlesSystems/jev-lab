# Offline baseline evidence

The committed `evidence/offline-baseline.jsonl` records a baseline-only run over all 30 synthetic fixtures. Jev was not called, so every row records `jev_status: not_run`. This run cannot satisfy the Jev acceptance target.

The phrase baseline matched 10 of 20 held-out labels. The review-all baseline matched 0 of 20 because the held-out labels contain only clear commitments and clear non-commitments. The fixture file SHA-256 is `60a55ee369176b0f561d1cf203829392a7f289bc2a107f49e3372dcc66ff7a09`.

An independent AI review checked the synthetic labels and their 10 commitment and 10 non-commitment composition. Human validation remains pending. The reviewed set replaced an earlier set with near-paraphrases before any live Jev measurement.

Reproduce the run.

```sh
python3 demos/promise_catcher/promise_catcher.py evaluate \
  --fixtures demos/promise_catcher/fixtures.jsonl \
  --evidence demos/promise_catcher/evidence/offline-baseline.jsonl
```

Live latency, usage, cost, and accuracy remain unmeasured because this implementation session had no API key. A live held-out run passes the proposed target only if it surfaces at least 7 of 10 commitments and makes at most one false suggestion across 10 non-commitments.
