#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Use virtual env if it exists
if [ -d .venv ]; then
    PYTHON=.venv/bin/python
else
    PYTHON=python3
fi

# Always run init — the script itself skips if data already exists.
# This ensures demo data is populated even after an auto-migration
# (database.py's init_db drops stale tables and recreates them empty).
echo "Initializing demo data..."
$PYTHON init_demo.py

echo "Starting server..."
exec $PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload