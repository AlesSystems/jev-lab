---
name: Launch Lab
description: A calm release-readiness dashboard for weighing synthetic signals against evidence.
colors:
  primary: "#3159da"
  ink: "#192642"
  canvas: "#f6f7fb"
  surface: "#fff"
  line: "#e2e7f0"
  blocked: "#fff0ee"
  supported: "#eaf5ed"
  review: "#fff5df"
typography:
  display:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "clamp(32px, 3.5vw, 48px)"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.03em"
  countdown:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "46px"
    lineHeight: 1.05
    letterSpacing: "-0.025em"
  body:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "16px"
    lineHeight: 1.5
rounded:
  control: "9px"
  card: "13px"
  panel: "16px"
spacing:
  card-gap: "13px"
  column-gap: "26px"
  section-gap: "35px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "14px 15px"
  metric-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "18px"
---

# Launch Lab design

## Overview

**Use scene.** A developer has a few minutes before a fictional launch. The dashboard should let them scan telemetry, find the underlying tests, challenge reassuring language, and see the distinction between Jev's judgment and a hard release rule.

**Visual direction.** Quiet light workspace, deep ink text, cobalt for actions and chart lines. Generous gaps separate the release hero, three data charts, evidence cards, and the checklist rail. No illustrations compete with the evidence. A narrow screen stacks the rail below the investigation so the task remains usable.

## Colors

Cobalt marks selected tabs, buttons, links, and chart lines. White panels sit on a cool pale canvas. The readiness panel uses restrained red, green, or amber backgrounds to distinguish blocked, supported, and review states.

## Typography

Space Grotesk carries headings, readiness, and the tabular countdown. DM Sans carries controls, notes, and evidence. The countdown is larger than the metric values so the launch deadline reads first. It scales to 36px on narrow screens.

## Layout

The desktop shell is capped at 1320px. Investigation and checklist form a two-column grid with a 318px rail. The three synthetic metrics form an even row; evidence forms two columns. Below 1000px, the rail stacks beneath the investigation. Below 650px, metrics and evidence become single-column lists.

## Elevation & Depth

Panels use pale borders at rest. Metric cards lift with a soft offset shadow on hover; the details drawer has a deeper offset shadow to signal its temporary layer.

## Shapes

Controls use compact corners. Data cards use moderately rounded corners, while the hero and checklist rail use the broadest panel corners. Small status marks remain circular.

## Components

**Interaction.** Release tabs reset the selected evidence and assessment. Every chart opens one keyboard-reachable details drawer with its six values and associated notes/tests. Evidence checkboxes update the selected count and clear any prior assessment and request reassessment. Reassessment shows loading, success, and actionable failure states. Mode switching also clears the prior result. Aborted requests cannot overwrite a newly selected release. The exact canonical request and typed answers are inspectable in a disclosure near the decision.

## Do's and Don'ts

**Decision boundary.** Required test statuses live in the prepared release catalog, independent of checkbox selection. A failure, flake, or missing required test always blocks a release. Passing test text reaches Jev only if its evidence card is selected. Metric descriptions do not leak explanatory notes into the model state. The fixture source is always labeled; live errors never silently turn into fixture answers.
