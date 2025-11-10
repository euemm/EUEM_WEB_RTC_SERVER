#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
	echo "Virtual environment not found at $VENV_DIR" >&2
	echo "Please create it (python -m venv venv) and install dependencies." >&2
	exit 1
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

export PYTHONPATH="$ROOT_DIR"

pytest "${@:-tests/test_database_connection.py tests/test_turn_credentials.py tests/test_websocket_handler.py}"
