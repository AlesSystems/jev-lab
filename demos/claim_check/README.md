# Claim check

Claim check holds one evidence passage still and swaps the claim in front of it. Keyword overlap is the baseline. The scenario verdict is a fixture. The page does not publish a release.

Without `TYPESAFE_API_KEY`, the page stays on that baseline. With the key, the server asks `jev-1.13.0` to choose `supported`, `contradicted`, or `insufficient_evidence`. A confidence below 0.80 stays in review. A failed call stays unavailable and is not replaced by the baseline. The key stays on the server.

```sh
python3 demos/claim_check/claim_check.py serve
TYPESAFE_API_KEY=... python3 demos/claim_check/claim_check.py serve
```

Open http://127.0.0.1:8766

```sh
python3 -m unittest demos/claim_check/test_claim_check.py
```
