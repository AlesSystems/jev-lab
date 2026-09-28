---
name: Jev Lab sheets
description: Construction-grid sheets for local decision demos.
colors:
  paper: "#f4f6f8"
  sheet: "#ffffff"
  ink: "#12151a"
  muted: "#243044"
  grid: "#b7c6e0"
  cobalt: "#1d4ed8"
  disabled: "#d5dbe3"
typography:
  display:
    fontFamily: "Barlow Condensed, Avenir Next Condensed, sans-serif"
    fontSize: "4.5rem"
    fontWeight: 600
    lineHeight: 0.85
    letterSpacing: "-0.03em"
  body:
    fontFamily: "Barlow, Avenir Next, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "-0.03em"
rounded:
  control: "14px"
  field: "12px"
spacing:
  page: "32px"
  cell: "12px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
  button-primary-hover:
    backgroundColor: "{colors.cobalt}"
    textColor: "{colors.paper}"
  decision-word:
    fontFamily: "{typography.display.fontFamily}"
    fontSize: "{typography.display.fontSize}"
    textColor: "{colors.ink}"
---

## Overview

Local demo pages are construction sheets. A monumental word states the decision. The baseline and the fixture label sit on the same grid. Cobalt marks a disagreement and never replaces the word.

## Color

Daylight desk. Cool white paper, white sheet, near-black ink, faint blue grid. Cobalt is the disagreement mark and the primary hover. Disabled controls use a light fill with the same ink as secondary text.

## Typography

Barlow for titles, body, and controls. Barlow Condensed only for the decision word and column labels. The decision word is uppercase at 4.5rem, and 2.4rem below 800px. Body measure stays near 68ch.

## Layout

One column of title, decision word, one control, then the sheet. No sidebar. Tables become stacked rows below 800px. Three-bay and three-cell sheets stack the same way.

## Components

Buttons are ink or outline, radius 14px. The pressed choice is filled ink. A disagreed cell uses a dashed cobalt outline. The grid is the sheet's measurement armature, not a backdrop behind marketing sections.

## Motion

Changing the decision word blurs for 200ms and settles. Content stays visible. Nothing animates on load.
