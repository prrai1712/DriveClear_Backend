#!/usr/bin/env bash
# Deploy DriveClear Backend to Render via Blueprint.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Checking git remote..."
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "No git remote 'origin'. Push this repo to GitHub first — see GITHUB.md"
  exit 1
fi

echo "==> Pushing latest main to GitHub..."
git push origin main

if command -v render >/dev/null 2>&1; then
  echo "==> Validating render.yaml..."
  if render whoami >/dev/null 2>&1; then
    render blueprints validate render.yaml
    echo "Blueprint file is valid."
  else
    echo "Render CLI not logged in. Run: render login"
  fi
else
  echo "Install Render CLI: brew install render"
fi

REPO_URL="$(git remote get-url origin | sed -E 's#git@github.com:#https://github.com/#; s#\.git$##')"
echo ""
echo "==> Next: create the Blueprint in Render"
echo "1. Open: https://dashboard.render.com/blueprint/new"
echo "2. Connect GitHub repo: $REPO_URL"
echo "3. Root Directory: leave EMPTY"
echo "4. Blueprint file: render.yaml"
echo "5. Review services (driveclear-mysql, driveclear-redis, driveclear-api) → Deploy"
echo ""
echo "After deploy, set secrets in driveclear-api → Environment (see DEPLOY.md)."
echo "Health check: curl https://driveclearbackend-production.up.railway.app/api/v1/health/"
