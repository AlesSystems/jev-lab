# Claim check

Claim check holds one evidence passage still and swaps the claim in front of it. Keyword overlap is the baseline. The scenario verdict is a fixture. The page does not call Jev, and it does not publish a release.

```sh
python3 demos/claim_check/claim_check.py serve
```

Open http://127.0.0.1:8766

```sh
python3 -m unittest demos/claim_check/test_claim_check.py
```
