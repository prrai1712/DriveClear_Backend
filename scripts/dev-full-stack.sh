#!/usr/bin/env bash
# Start backend (:8000) + frontend (:3000) when both repos are sibling folders
set -euo pipefail
BACKEND_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_ROOT="$(cd "$BACKEND_ROOT/../DriveClear_Frontend" 2>/dev/null && pwd || true)"

if [[ ! -d "$FRONTEND_ROOT" ]]; then
  echo "DriveClear_Frontend not found at ../DriveClear_Frontend"
  echo "Clone the frontend repo as a sibling folder, or run frontend separately with npm run dev"
  exit 1
fi

pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 1

echo "Starting Django on http://localhost:8000 ..."
(cd "$BACKEND_ROOT" && .venv/bin/python manage.py runserver 0.0.0.0:8000) &
BACK_PID=$!

echo "Starting Next.js on http://localhost:3000 ..."
(cd "$FRONTEND_ROOT" && npm run dev) &
FRONT_PID=$!

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null' EXIT

echo ""
echo "DriveClear is running:"
echo "  App:     http://localhost:3000"
echo "  Login:   http://localhost:3000/login"
echo "  API:     http://localhost:8000/api/v1/health/"
echo ""
wait
