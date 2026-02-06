#!/bin/bash
# Launcher script for OpenVPN Manager

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    # Activate virtual environment and run
    source "$VENV_DIR/bin/activate"
    python3 main.py
else
    echo "Virtual environment not found!"
    echo "Please run ./setup.sh first to set up the environment."
    exit 1
fi

