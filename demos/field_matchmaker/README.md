# Field match

Field match previews how a CSV maps onto five accepted fields. Load an example or paste a CSV, then click **Suggest mapping**. Example selection does not call the API. Custom input accepts 1–10 unique columns, 1–20 data rows, up to 12000 characters and 500 characters per cell. Jev sees headers and the first three data rows. Custom CSVs have no fixture labels. Locking a mapping does not import the file.

Without `TYPESAFE_API_KEY`, the page stays on that baseline. With the key, the server asks `jev-1.13.0` to choose a field, or `unmapped`, for each column. A confidence below 0.80 stays unmapped for review. Adjust the mapping selects and click **Lock mapping** after validation finishes. Duplicate targets are rejected in code; edits invalidate the previous preview immediately. A failed call does not fill the picks from the alias list. The key stays on the server.

```sh
python3 demos/field_matchmaker/field_matchmaker.py serve
TYPESAFE_API_KEY=... python3 demos/field_matchmaker/field_matchmaker.py serve
```

Open http://127.0.0.1:8765

```sh
python3 -m unittest demos/field_matchmaker/test_field_matchmaker.py
```
