# Claim check

Claim check compares an editable claim with an editable evidence passage. Choose an example, edit either field, and select **Run claim check**. Loading an example does not call Jev. Keyword overlap is shown beside the Jev result. The page does not publish a release.

Without `TYPESAFE_API_KEY`, the page explicitly shows **BASELINE ONLY**. Custom checks never carry a fixture label. The original fixture board API and CLI retain their scenario labels. With the key, the server asks `jev-1.13.0` to choose `supported`, `contradicted`, or `insufficient_evidence`. A confidence below 0.80 stays in review. A failed call stays unavailable and is not replaced by the baseline. The key stays on the server.

```sh
python3 demos/claim_check/claim_check.py serve
TYPESAFE_API_KEY=... python3 demos/claim_check/claim_check.py serve
```

Open http://127.0.0.1:8766

```sh
python3 -m unittest demos/claim_check/test_claim_check.py
```

Custom checks use `POST /api/check` with a JSON object containing `claim` (up to 2,000 characters) and `evidence` (up to 12,000 characters). Both fields are required.
