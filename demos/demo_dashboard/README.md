# Demo dashboard

One local page for the nine Jev Lab demos. Switch a demo and read its Jev call shape. The page does not call Jev. Answer values in the catalog are blank. The catalog is the extension point: add or change one object in `catalog()`.

```sh
python3 demos/demo_dashboard/demo_dashboard.py serve
```

Open http://127.0.0.1:8769

```sh
python3 -m unittest demos/demo_dashboard/test_demo_dashboard.py
```
