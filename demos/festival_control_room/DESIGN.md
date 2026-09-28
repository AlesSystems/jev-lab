---
name: Festival Control Room
description: A functional venue map for comparing synthetic dispatch plans.
colors:
  ground: "#f7f7f2"
  paper: "#fffefa"
  map: "#e7eee2"
  map-zone: "#dce8d8"
  source-badge-fill: "#e8f1e5"
  source-badge-ink: "#4b7055"
  forest-ink: "#20372d"
  forest-action: "#28513c"
  medical-green: "#2c674c"
  security-blue: "#43697a"
  welfare-brown: "#896c4c"
  operations-olive: "#626a53"
  incident-red: "#c95038"
  separator: "#dce3d7"
  disabled: "#9ba9a0"
typography:
  title:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "17px"
    fontWeight: 750
    lineHeight: 1.2
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "12px"
  map-label:
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "22px"
    fontWeight: 750
rounded:
  panel: "8px"
  control: "6px"
  badge: "5px"
  pill: "4px"
spacing:
  compact: "8px"
  section: "16px"
  rail: "18px"
  frame: "22px"
components:
  button-primary:
    backgroundColor: "{colors.forest-action}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.control}"
    height: "44px"
  map-panel:
    backgroundColor: "{colors.map}"
    rounded: "{rounded.panel}"
  source-badge:
    backgroundColor: "{colors.source-badge-fill}"
    textColor: "{colors.source-badge-ink}"
    rounded: "{rounded.badge}"
---

# Design System: Festival Control Room

## Overview

**Creative North Star: "The Venue Desk"**

A light, functional site plan is the main workspace. Warm paper holds controls and report evidence; green ground holds the venue. The map, incident rail, and persistent transport make staffing changes and replay readable at a glance. This is a synthetic simulation, so the design shows provenance and status alongside each decision.

**Key Characteristics:** clear site geometry, compact evidence, one persistent timeline, direct manipulation of crew starting positions.

## Colors

Forest ink and action green carry ordinary controls. Incident red is reserved for report pins, event ticks, and urgent focus; crew markers use stable specialty colors. Pale green distinguishes map zones, and warm paper keeps the dense rail legible. Disabled crews turn gray. Separators are thin and quiet.

**The State Color Rule.** Keep incident red distinct from crew specialty colors and from the green venue ground; color always has a status or identity role.

## Typography

One Inter-first sans-serif stack serves the whole interface. The map heading is compact and firm; report details and controls use a 12px base. Time values use tabular numerals. SVG place labels are larger than rail labels because the map is the primary reading surface; the mobile rule enlarges them to 38 SVG units for legibility at the smaller rendered scale.

**The Map Label Rule.** Keep place names readable on the map at every breakpoint; do not move the drag hint into the SVG where scaling makes it too small.

## Layout

At desktop widths, a 66px header sits above a map and 344px right rail, with a 128px transport below. The map flexes to fill available space. At 850px and below, the map comes first, the rail follows, and transport sticks to the bottom. At 520px the map has a 390px height and controls compress while retaining visible labels. The SVG uses a 1000 × 700 coordinate space for venue zones and draggable crew positions.

**The Replay Rule.** The map and timeline stay in view while staffing changes rerun the same reports. The rail explains selected incidents without replacing the map.

### Architecture behind replay

Reports, judgments, crews, and assignments are explicit records. Jev provides urgency, team specialty, and evidence judgments. Python owns the waiting queue, available crews, travel, service duration, confidence gates, and safety thresholds. JavaScript renders the immutable schedule and interpolates movement. Two independent Sol low design explorations considered server-generated schedules and full frame snapshots. A Sol high cross-review favored the schedule because arbitrary scrubbing and smooth movement need interpolation in either design. Each assignment carries authoritative dispatch, arrival, and clear times, plus origin and destination. This avoids dense frame payloads and duplicated dispatch logic in the browser.

Straight-line travel is sufficient for this demonstration. A walkable route graph belongs in a future version only if barriers or real route choices need to be shown.

## Elevation & Depth

The interface is flat. Background changes and thin borders separate map, rail, rows, and transport; the crew swatch has a small inset ring. There are no floating card shadows.

## Shapes

Panels use gently rounded corners; controls and badges use smaller radii. Incident and crew markers are circles, with a halo for the active crew. Routes are dashed lines. Venue buildings and zones use simple rectilinear geometry.

## Components

### Controls

The primary replay button uses forest green with white text; secondary buttons and selectors use paper with a green-gray border. Controls are at least 44px high. Hover lightens the surface. Keyboard focus uses a visible red outline; disabled controls reduce opacity.

### Map and markers

The map is a pale green SVG panel with named zones. Incident pins use red with a light inner dot; selected pins gain a darker stroke and resolved pins fade. Crew markers use specialty color, gray when disabled, and a translucent halo while dragging. Routes are dashed. The drag hint remains outside the SVG so its text does not shrink with the venue coordinate system.

### Report rail

Flat report rows use thin separators and a pale selected state. Small pills identify fixture, live, and review states. Each selected report exposes urgency, team, and evidence values beside its assignment status. Crew rows include a colored swatch and an enabled toggle.

### Replay transport

The bottom transport keeps play, reset, speed, a range slider, event ticks, and response comparison together. Incident ticks are red; clear ticks are muted green. Motion follows simulation time; reduced-motion preference suppresses decorative transitions.

## Do's and Don'ts

### Do:

- **Do** keep the map dominant and the report evidence visible in the rail.
- **Do** retain labeled controls, keyboard focus, and the 44px control target floor.
- **Do** show crew starting positions separately from their moving replay positions.

### Don't:

- **Don't** imply straight-line travel is a real venue route. It is the demo's deterministic travel approximation.
- **Don't** replace the server-produced dispatch schedule with browser-calculated assignments.
