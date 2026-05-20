#!/usr/bin/env bash
# Always use project venv (fixes "No module named firebase_admin")
set -e
cd "$(dirname "$0")"
exec .venv/bin/python manage.py "$@"
