# Repository Guidelines

## Project Structure & Module Organization
Repo contents: `src/jeongsimulator/` for runtime modules, `tests/` for specs (split into `tests/unit/` and `tests/integration/` when needed), and `scripts/checks.sh` for automation. Add code under `src/jeongsimulator/<component>.py`, mirror it with `tests/<scope>/test_<component>.py`, and reserve the root for configs like `pyproject.toml`, `uv.lock`, or `.python-version`. Docs live in `docs/`, experiments in `notebooks/`, reusable assets in `assets/`.

## Build, Test, and Development Commands
Use uv: `UV_CACHE_DIR=.uv-cache uv sync` installs dependencies into `.venv`, and `uv run <cmd>` executes tooling. Primary commands are `uv run pytest` (unit tests), `uv run ruff check src tests` (lint), and `uv run jeongsimulator` (smoke launch). `scripts/checks.sh` runs them sequentially; keep it current whenever new mandatory checks appear.

## Coding Style & Naming Conventions
Target Python 3.10+, keep 4-space indentation, and prefer explicit type hints plus docstrings on public functions. Use snake_case for functions and variables, PascalCase for classes, and SCREAMING_SNAKE_CASE for constants. Keep modules cohesive (~300 lines max) and organize subpackages such as `agents/`, `metrics/`, or `ui/` inside `src/jeongsimulator/`. Autoformat with `uv run ruff format` (or `ruff check --fix`) before sharing changes.

## Testing Guidelines
Practice strict test-driven development: add or update tests in `tests/unit/` or `tests/integration/` before implementing behavior. Follow `test_<subject>.py` filenames and `test_<expectation>` functions, rely on `pytest-randomly` for reproducibility, and grow coverage toward ≥90% as modules mature. All tests must pass via `uv run pytest` and inside `scripts/checks.sh`.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (e.g., `feat(cli): add scenario flag`). Each commit should capture one logical change plus matching tests/docs. Pull requests must describe context, solution, validation, attach screenshots or logs when behavior changes, link issues with `Fixes #<id>`, and include the latest `scripts/checks.sh` output.

## Operational Rules for Agents
- Ensure reactivity: when touching any UI or observable surface, wire callbacks/state updates so visuals reflect changes immediately; no stale displays.
- Enforce TDD: start with a failing test, implement the minimum code to pass, then refactor once green.
- Do not consider a task complete until `scripts/checks.sh` finishes with all sections reporting "All checks passed".

## Security & Configuration Tips
Keep secrets in `.env` (gitignored) and load them through a typed settings layer such as `pydantic-settings` once introduced. Validate any YAML/JSON scenario files with helper scripts before launching long simulations. Pin dependency versions in `pyproject.toml`/`uv.lock`, audit additions with `uv run pip-audit` (or similar), and record external API requirements in `docs/security.md` for future operators.
