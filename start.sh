#!/bin/bash

set -e

export PYTHONPATH
PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."

exec python src/main.py