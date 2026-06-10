#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Use virtual env if it exists
if [ -d .venv ]; then
    PYTHON=.venv/bin/python
else
    PYTHON=python3
fi

# Init DB if not exists
if [ ! -f activity.db ]; then
    echo "Initializing demo data..."
    $PYTHON init_demo.py
fi

echo "Starting server..."
exec $PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload