#!/usr/bin/env bash
# Run Django migrations against local Homebrew MySQL (no Docker)
# Prerequisite: run scripts/init_mysql_local.sql in DataGrip as root first
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DJANGO_SETTINGS_MODULE=config.settings.local

echo "==> Checking MySQL connection (from .env)..."
.venv/bin/python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()
from django.db import connection
connection.ensure_connection()
print('OK:', connection.settings_dict['HOST'], connection.settings_dict['NAME'], 'as', connection.settings_dict['USER'])
"

echo "==> Running migrations..."
.venv/bin/python manage.py migrate --noinput

echo "==> Table count:"
.venv/bin/python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()
from django.db import connection
with connection.cursor() as c:
    c.execute('SHOW TABLES')
    tables = [r[0] for r in c.fetchall()]
    print(len(tables), 'tables')
    for t in sorted(tables)[:15]:
        print(' ', t)
    if len(tables) > 15:
        print('  ...')
"

echo ""
echo "Done. DataGrip: Host 127.0.0.1, Port 3306, DB driveclear, User driveclear, Password driveclear"
