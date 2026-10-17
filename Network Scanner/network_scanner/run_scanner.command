#!/bin/bash
# Double-click in Finder to start the Network Scanner with its own .venv.
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python main.py
