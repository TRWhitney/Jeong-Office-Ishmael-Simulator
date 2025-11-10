# JeongSimulator

Practice the Jeong Office Ishmael flow from **Limbus Company** through a turn-accurate simulator. The project provides a reusable simulation engine plus a rich CLI that mirrors the official mechanics so players (or bots) can rehearse optimal lines, visualize Bright progress, and script their own experiments.

## What You Get

- **Deterministic simulation core** (`src/jeongsimulator/simulation.py`) that models suits, Bright potency/count, card offers, streak bonuses, Defend/EGO, and full Kōzan resolution with injectable RNG.
- **Terminal UI** (`src/jeongsimulator/cli.py`) powered by `rich` that can run a non-interactive smoke loop (for CI) or interactive turns (for practice sessions).
- **Thorough tests** in `tests/unit/` that encode the spec in `spec.md`, keeping the behavior stable.
- **Automation script** (`scripts/checks.sh`) that chains unit tests, lint, and a smoke launch so contributions stay green.

## Simulation Mechanics (Quick Reference)

- **Suits**: Red, Yellow, Blue. Current suit is rolled on initialization and whenever a Bright cycle resets. Defend schedules a different suit for the next turn.
- **Bright**: Potency ranges 0–5 (cap 5), Count starts at 3 and ticks down each turn. Cycle resets when Potency hits 5 _or_ Count hits 0; resets clear streaks and reroll the suit.
- **Deck & Offer**: Default deck `[S1, S1, S1, S2, S2, S3]`. The ordered offer persists between turns and refills to two cards at the start of every turn. Using/discarding the first slot shifts the second forward.
- **Matching & streaks**: Using a card whose color matches the current suit grants +1 Bright (+1 extra if last turn also matched during the same cycle). S3 adds +1 potency whether it matches or not.
- **Actions**:
  - `Use First / Second`: Play the card in slot 1 or 2. Off-color cards remaining in the offer are discarded immediately.
  - `Defend (Counter)`: Discards the first slot, has a 50% chance to grant +1 Bright, and forces a different suit next turn.
  - `EGO`: Always matches and grants +2 Bright (plus streak bonus), discarding the first slot.
- **Kōzan finisher**: On cycle end with Bright ≥3, flips `min(potency, 5)` 95%-success coins, logs the sequence, then resets Bright to 0/3.

For the authoritative rule text, read `spec.md`.

## Repository Layout

- `src/jeongsimulator/`: Runtime package
  - `simulation.py`: Stateful `JeongSimulation` engine plus dataclasses for snapshots and results.
  - `cli.py`: Rich-powered CLI with smoke (`jeongsimulator`) and interactive loops.
- `tests/unit/`: Pytest coverage for both the CLI entry point and simulation rules.
- `scripts/checks.sh`: Aggregated pipeline (`pytest` → `ruff` → smoke run) that CI and contributors should use.
- `spec.md`: Design contract for the entire simulator.

## Getting Started

1. **Install uv** (https://github.com/astral-sh/uv) and ensure Python 3.10+ is available.
2. Sync dependencies into the local `.venv` (kept inside `.uv-cache`):

   ```bash
   UV_CACHE_DIR=.uv-cache uv sync
   ```

3. Activate the environment with `source .venv/bin/activate` (optional—`uv run` can also spawn commands directly).

## Running the Simulator

- **Smoke run (non-interactive)**: `uv run jeongsimulator`  
  The CLI auto-detects whether stdin/stdout are TTYs; in pipelines it defaults to a deterministic two-turn smoke test, printing each turn’s snapshot, auto action, and resolution.

- **Interactive turns**: run the command from a TTY (`uv run jeongsimulator`) or call `uv run python -m jeongsimulator.cli` to force interactive mode. Each turn shows the suit panel, available actions, and applies your input (`1`, `2`, `d`, `e`, `q`).

- **Embedding the engine**: Import `JeongSimulation` and drive it manually:

  ```python
  from jeongsimulator import JeongSimulation, Action

  sim = JeongSimulation()
  snapshot = sim.start_turn()
  resolution = sim.resolve(Action.USE_FIRST)
  end_state = sim.end_turn()
  ```

  Provide your own `random.Random` (or stub) to make runs deterministic for experiments or bots.

## Verification & Tooling

- **Unit tests**: `uv run pytest`
- **Lint/format**: `uv run ruff check src tests` (use `ruff check --fix` or `ruff format` when modifying code)
- **Smoke launch**: `uv run jeongsimulator`
- **All required checks**: `./scripts/checks.sh` (runs the three commands above and must end with “All checks passed.”)

Tests use `pytest-randomly`; re-run them until they pass consistently whenever you alter RNG-sensitive logic.

## Development Workflow

- Follow the guidelines in `AGENTS.md`: write or update tests first (TDD), keep modules small, and document public functions with type hints and docstrings.
- New runtime components belong under `src/jeongsimulator/<component>.py` with mirrored tests in `tests/<scope>/test_<component>.py`.
- Auto-format with `uv run ruff format` (or `ruff check --fix`) before committing.
- Use Conventional Commits (`feat(cli): ...`, `fix(simulation): ...`) and include the latest `scripts/checks.sh` output when opening a PR.
- Never commit secrets; keep run-time configuration in `.env` (gitignored) and document security considerations in `docs/security.md` if you add external integrations.

## Additional Resources

- `spec.md`: Full mechanic breakdown, pseudocode, and acceptance checklist.
- `tests/unit/test_simulation.py`: Practical examples that assert every rule (offer persistence, S3 bonus, streak handling, Defend/EGO behavior, Kōzan).
- `tests/unit/test_main.py`: CLI expectations (smoke run success, graceful Ctrl-C handling).

Use these references alongside the repository guidelines in `AGENTS.md` whenever you extend or reuse the simulator.
