# Field match

Field match previews how one synthetic CSV would map onto five accepted fields. The page runs an alias baseline beside hand-labeled scenario picks. It does not call Jev, and locking a mapping does not import the file.

```sh
python3 demos/field_matchmaker/field_matchmaker.py serve
```

Open http://127.0.0.1:8765

```sh
python3 -m unittest demos/field_matchmaker/test_field_matchmaker.py
```
