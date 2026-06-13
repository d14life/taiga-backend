#!/usr/bin/env bash
# Run the Тайга endpoint smoke-test suite against the live backend.
# Usage: tests/run.sh            (uses TAIGA_BASE, default http://127.0.0.1:8777)
#        TAIGA_BASE=http://127.0.0.1:9000 tests/run.sh
set -euo pipefail

# repo root = parent of this script's dir, so it works from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

exec python3 -m unittest tests.test_endpoints -v "$@"
