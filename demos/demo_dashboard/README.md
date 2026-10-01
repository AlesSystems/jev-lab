# Demo dashboard

One local page for the ten Jev Lab demos. Switch a demo and read its Jev call shape. The page does not call Jev. Answer values in the catalog are blank. The catalog is the extension point: add or change one object in `catalog()`.

```sh
python3 demos/demo_dashboard/demo_dashboard.py serve
```

Open http://127.0.0.1:8769

```sh
python3 -m unittest demos/demo_dashboard/test_demo_dashboard.py
```

Choose **Release Room** for the combined release and feedback workbench. Start its listed server, then follow the local link. The dashboard keeps static examples; actual responses appear inside each running demo.

For step-by-step checks of the dashboard and every demo, use the [developer testing guide](../../docs/testing-demos.md).
