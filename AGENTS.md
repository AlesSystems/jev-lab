# Repository Guidelines

## Project Structure & Module Organization

Jev Lab contains small, reproducible experiments with TypeSafe AI's Jev model. Each `demos/<demo_name>/` owns its Python entry point, `test_<demo_name>.py`, and README. Browser demos keep HTML, CSS, and JavaScript in `static/`, with acceptance screenshots in `screenshots/`. CLI demos include fixtures and recorded evidence. Research, evaluation guidance, and architecture diagrams live in `docs/`.

Before changing a demo, read its README. For UI work, consult its local `DESIGN.md` when present, otherwise the root `DESIGN.md`.

## Build, Test, and Development Commands

Run commands from the repository root. Demos use Python 3.10+ and the standard library; no package installation or build step is required. Node.js is used for JavaScript syntax checks.

- `python3 demos/launch_lab/launch_lab.py serve --port 8766` — start Launch Lab locally.
- `python3 demos/repro_coach/repro_coach.py fixtures --split dev` — evaluate the offline development fixtures.
- `python3 -m unittest demos/launch_lab/test_launch_lab.py` — run one demo's tests.
- `node --check demos/launch_lab/static/app.js` — check JavaScript syntax.
- `uvx ruff check demos/repro_coach` — run the documented Repro Coach lint check.
- `uvx mypy --check-untyped-defs demos/repro_coach/repro_coach.py` — check its Python types.

Use the all-suite runner in `docs/launch-feedback-acceptance.md` for cross-demo changes.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions and modules, `PascalCase` classes, and uppercase constants. Follow neighboring type annotations and quote style. JavaScript uses two-space indentation and `camelCase` names. Keep demos self-contained and prefer standard-library solutions. No repository-wide formatter configuration is committed.

## Testing Guidelines

Tests use `unittest` and `unittest.mock`; name files and methods `test_*`. Keep tests deterministic and runnable without an API key. Cover changed behavior, malformed inputs, API failures, and stale UI state where relevant. No numeric coverage threshold is configured. Verify UI changes in desktop and mobile browsers and capture screenshots.

## Commit & Pull Request Guidelines

Use imperative Conventional Commits, matching history: `feat(launch-lab): ...`, `fix(festival): ...`, or `docs(demos): ...`. Keep each commit focused on one behavior. Run focused tests and relevant lint before handoff. PRs should explain behavior and risk, link the relevant issue, roadmap item, or acceptance document, list verification and limitations, and include UI screenshots. Call out security, privacy, schema, or deployment impacts when applicable.

## Security & Research Evidence

Keep `TYPESAFE_API_KEY` in the server environment and servers bound to loopback. Never commit secrets or expose keys to browsers. Label synthetic fixtures and offline baselines explicitly; API failures must remain errors. Record measured results separately from assumptions using `docs/evaluation.md`.
