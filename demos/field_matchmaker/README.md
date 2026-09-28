# Field match

Field match previews how one synthetic CSV would map onto five accepted fields. The page runs an alias baseline beside hand-labeled scenario picks. Locking a mapping does not import the file.

Without `TYPESAFE_API_KEY`, the page stays on that baseline. With the key, the server asks `jev-1.13.0` to choose a field, or `unmapped`, for each column. A confidence below 0.80 stays unmapped for review. Duplicate targets are still rejected in code. A failed call does not fill the picks from the alias list. The key stays on the server.

```sh
python3 demos/field_matchmaker/field_matchmaker.py serve
TYPESAFE_API_KEY=... python3 demos/field_matchmaker/field_matchmaker.py serve
```

Open http://127.0.0.1:8765

```sh
python3 -m unittest demos/field_matchmaker/test_field_matchmaker.py
```
