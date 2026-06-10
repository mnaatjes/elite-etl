#!/bin/bash
# .scripts/run_tests.sh
# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run pytest on the tests directory
# We set PYTHONPATH to include src so imports work
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/
