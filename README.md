# Jev Lab

Small, real, and reliable experiments with [Jev](https://typesafe.ai/), TypeSafe AI's model for fast, typed decisions inside software.

This repository documents what Jev is useful for, where its limits appear, and how to build practical integrations that are easy to understand and reproduce.

## Goals

- Research Jev's behavior, capabilities, and trade-offs.
- Build focused demos around real use cases.
- Record results, limitations, latency, cost, and reliability where relevant.
- Keep every example small enough to inspect and reproduce.

## Demos

For start commands and a short walkthrough of every local page, see [Run the UI demos](docs/ui-demos.md).

Start with the [demo idea shortlist](docs/demo-ideas.md): eight small experiments for developer tools, SaaS workflows, and automations. Each includes a concrete input, Jev's decision, a simpler baseline, and a success check.

Recommended first experiment: [Repro Coach](docs/first-demo-repro-coach.md), which checks bug reports for missing information and selects a fixed follow-up template.

See each demo's linked documentation for implementation and validation status. No live Jev results have been recorded yet.

Three shortlist ideas also have a local page. Each page shows a baseline beside a fixture label. Set `TYPESAFE_API_KEY` before starting the page to ask Jev; without the key, the page stays on the baseline.

- [Field match](demos/field_matchmaker/README.md)
- [Claim check](demos/claim_check/README.md)
- [Interruption budget](demos/interruption_budget/README.md)

[Festival Control Room](demos/festival_control_room/README.md) is a map-based simulation. Replay volunteer reports, move crews, and change staffing to compare dispatch plans. It starts with labeled fixture judgments and supports live Jev urgency, team, and evidence judgments when `TYPESAFE_API_KEY` is set.

Two evidence workbenches let you change the inputs and inspect the resulting judgments:

- [Launch Lab](demos/launch_lab/README.md) asks whether you would ship one of three fictional releases. Inspect synthetic charts, choose evidence, and compare Jev's assessment with required test rules.
- [Feedback Kitchen](demos/feedback_kitchen/README.md) matches noisy feedback to a fixed catalog of improvements. Edit comments, inspect supporting evidence, and collect improvements in a tray.

Both run with Python's standard library and a browser. Offline results are labeled baselines. Set `TYPESAFE_API_KEY` in the server environment to request live Choice, Score, and Noul judgments.

[Jev Habitat](demos/jev_habitat/README.md) is a separate room simulation. Turn a request into typed judgments, inspect the API exchange, adjust a local decision threshold, and apply a change to simulated lights, music, or blinds. Prepared examples work offline. Free text uses live Jev.

The [demo dashboard](demos/demo_dashboard/README.md) lists the local pages and the two command-line demos on one warm desk. Switch a demo, then read the request shape beside a blank response. It does not call Jev.

## Research notes

- [Where Jev fits](docs/jev-fit.md) — primitives, integration boundaries, limitations, and dated primary sources.
- [Shared demo architecture](docs/diagrams/jev-decision-loop.html) — a standalone visual of the application/Jev boundary. Open the HTML file locally; GitHub displays its source.
- [How to evaluate a demo](docs/evaluation.md) — compare against simple code, measure uncertainty, and record evidence.

Research notes distinguish observed results from assumptions and vendor claims. Research snapshot: **2026-09-22**.

## Resources

- [TypeSafe AI](https://typesafe.ai/)
- [Projects built with Jev](https://jevable.com/)

## License

Released under the [MIT License](LICENSE).

> Jev Lab is an independent community project and is not affiliated with or endorsed by TypeSafe AI.
