---
name: Feedback Kitchen
description: A warm workbench for turning noisy app feedback into supported improvements.
colors:
  primary: "#ad3f22"
  ink: "#392b25"
  canvas: "#fcf8ef"
  line: "#e5dacb"
  oat-card: "#f6e7cf"
  sage-card: "#e7eee1"
  rose-card: "#f4e3dc"
typography:
  display:
    fontFamily: "Fraunces, serif"
    fontSize: "clamp(48px, 5.6vw, 88px)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.038em"
  body:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "17px"
    lineHeight: 1.55
  column-title:
    fontFamily: "Fraunces, serif"
    fontSize: "27px"
    lineHeight: 1.1
rounded:
  control: "10px"
  feedback: "12px"
  suggestion: "14px"
spacing:
  column-gap: "24px"
  card-gap: "9px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#fff"
    rounded: "{rounded.control}"
    padding: "12px 19px"
  feedback-card:
    backgroundColor: "{colors.oat-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.feedback}"
    padding: "16px"
---

# Feedback Kitchen design

## Overview

An operate-mode workbench for comparing raw customer language with specific product proposals. The three-column path is Inbox → Suggested improvement → Evidence. A warm cream canvas, orange action color, and rotating pale card tints make it feel like sorting notes at a table, distinct from a release dashboard. Fraunces provides expressive headings; DM Sans keeps dense feedback readable. Each selected suggestion shows a corpus-level support judgment and the comments Jev matched to it. The distinction is deliberately visible because a matched complaint may still fail to establish a proposed cause.

## Colors

Burnt orange identifies the primary action and selected details. Dark warm ink and a cream canvas keep longer comments comfortable to read. Oat, sage, and rose tints distinguish adjacent feedback cards without assigning them a semantic verdict.

## Typography

Fraunces supplies the large editorial introduction and column headings. DM Sans keeps feedback, controls, and evidence compact and legible. The main introduction uses a responsive size up to 88px, while column headings use 27px.

## Layout

The workspace is a three-column grid at desktop width inside a 1550px maximum shell. Thin vertical rules make the Inbox → Suggested improvement → Evidence sequence explicit. Below 1050px the arrangement adapts; below 650px columns stack in the same reading order.

## Elevation & Depth

Cards are mostly flat on the cream field. The selected feedback card receives a soft offset shadow; hover movement is brief and suppressed for reduced motion.

## Shapes

Feedback cards use gentle 12px corners, suggestion cards 14px, and primary controls 10px. Product selectors are pills because they are compact mutually exclusive controls.

## Components

Buttons expose pressed states, status updates are announced, and every edit clears judgments until reassessment. The inspection disclosure is the audit path from the shown verdict to the exact live request and answers.

## Do's and Don'ts

Keep a visible distinction between a comment matching a proposal and evidence supporting its cause. Use the pale card tints for variety in the inbox, not as risk or impact ratings.
