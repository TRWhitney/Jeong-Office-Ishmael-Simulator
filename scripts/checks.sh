#!/usr/bin/env bash
# Aggregate verification script: tests → lint → smoke run.
set -euo pipefail

PROJECT_ROOT=$(cd -- "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
cd "$PROJECT_ROOT"

UV_BIN=${UV_BIN:-uv}
export UV_CACHE_DIR=${UV_CACHE_DIR:-.uv-cache}

run_uv() {
  "$UV_BIN" run "$@"
}

section() {
  echo
  echo "=== $1 ==="
}

section "Running unit tests"
run_uv pytest

section "Running ruff"
run_uv ruff check src tests

section "Running smoke launch"
run_uv jeongsimulator

echo
printf 'All checks passed.\n'
