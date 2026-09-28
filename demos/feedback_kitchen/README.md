# Feedback Kitchen

A local, fictional product feedback workbench. Pick a product, inspect eight comments and a closed improvement catalog, and collect up to three choices. The prepared baseline is an **illustrative fixture**, not a Jev result. Editing or adding feedback clears every old judgment; use the live assessment to evaluate changed text.

```sh
python3 demos/feedback_kitchen/feedback_kitchen.py serve --port 8767
```

Open [http://127.0.0.1:8767](http://127.0.0.1:8767). To assess with the TypeSafe API, start the server with a key in its environment:

```sh
TYPESAFE_API_KEY=your_key_here python3 demos/feedback_kitchen/feedback_kitchen.py serve --port 8767
```

The server sends one Jev request per assessment. Choice matches each comment to one catalog improvement, `unclear`, or `no_match`. Score rates practical disruption on a 0–3 rubric. Noul judges whether the **entire current comment collection** supports each specific improvement claim. The Evidence column shows matching comments and corpus-level claim support separately. The inspection disclosure shows the exact request and response from a live assessment. No key is sent to the browser. A failed API call remains an error rather than silently reverting to fixture data.

For the recipe example, the initial lost-list comments describe a real problem but not its cause. Edit a comment to “My saved list disappears whenever I lose mobile signal,” then reassess. That new claim can support offline access; an empty list alone cannot prove it. This illustrates evidence quality, not a validated product recommendation.

The server binds to loopback only. It has no accounts, persistence, public deployment configuration, or measured calibration for the displayed probabilities. The products and feedback are synthetic.

```sh
python3 -m unittest demos/feedback_kitchen/test_feedback_kitchen.py
node --check demos/feedback_kitchen/static/app.js
```

API design follows the TypeSafe [HTTP reference](https://docs.typesafe.ai/api), [Choice](https://docs.typesafe.ai/primitives/choice), [Score](https://docs.typesafe.ai/primitives/score), and [Noul](https://docs.typesafe.ai/primitives/noul) documentation.
