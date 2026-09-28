# Product

<!-- impeccable:product-schema 1 -->

Assumptions below are inferred from the repository and the request to build the three local UI demos. They are not a separate interview.

## Platform

web

## Stack

delegated: one Python 3 stdlib program and one static page per demo. The existing demos are local Python. The pages stay local. No framework, database, or deployed app.

## Users

A developer evaluating Jev, at a laptop, comparing a simple baseline with a hand-labeled scenario for one narrow workflow.

## Product Purpose

Jev Lab shows where a typed decision model helps inside ordinary software, and where simpler code is enough. Success for these three demos is a page where the comparison is visible without reading a terminal log.

## Positioning

Each demo keeps the decision, the baseline, and the hand-labeled scenario on one page. The page does not present baseline output as a Jev result.

## Operating Context

Local Python, synthetic fixtures, and a browser on the same machine. The existing command-line demos remain the evaluation path. These pages are the visible comparison.

## Capabilities and Constraints

The three workflows are CSV field matching, release-claim checking, and interruption budgeting. Each page runs its baseline in process. Scenario labels are fixtures. Live Jev calls stay out of these pages. Confirming a mapping, a claim reading, or a quiet-hours bucket never imports data, publishes a release, or sends a notification. No customer records.

## Brand Commitments

The project name is Jev Lab. It is an independent community project and is not affiliated with or endorsed by TypeSafe AI.

## Evidence on Hand

Synthetic scenarios only. No live Jev measurements exist in this repository. Do not invent accuracy, latency, or cost figures.

## Product Principles

- Show the comparison, not a claim about the model.
- Keep each demo able to merge without editing the others.
- Leave uncertain and conflicting states on the page.
- Prefer a short local loop over a product shell.
