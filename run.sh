#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Virtual environment not found. Create it and run: pip install -e ."
  exit 1
fi
exec .venv/bin/python -m softhsm_studio
