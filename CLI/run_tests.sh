#!/bin/bash
# Script pour lancer les tests avec le bon PYTHONPATH

cd "$(dirname "$0")"
PYTHONPATH=. ../venv/bin/python -m pytest "$@"
