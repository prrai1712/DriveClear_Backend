#!/usr/bin/env bash
# One-command free deploy: Aiven MySQL (free) + Render web (free).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RENDER_OWNER="tea-d3vkkp75r7bs738a79lg"
RENDER_SERVICE="srv-d86u5gd7vvec73amkjt0"
RENDER_API_URL="https://driveclear-api.onrender.com"
AIVEN_PROJECT="${AIVEN_PROJECT:-driveclear}"
AIVEN_SERVICE="${AIVEN_SERVICE:-driveclear-mysql}"
AIVEN_CLOUD="${AIVEN_CLOUD:-google-asia-southeast1}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need avn
need python3
need curl

API_KEY="$(python3 -c "import yaml; print(yaml.safe_load(open('$HOME/.render/cli.yaml'))['api']['key'])")"

echo "==> Checking Aiven login..."
if ! avn user info >/dev/null 2>&1; then
  echo "Run once: avn user login   (Sign in with Google — no credit card)"
  exit 1
fi

echo "==> Ensuring Aiven project: $AIVEN_PROJECT"
if ! avn project list --format json | python3 -c "import sys,json; import sys; d=json.load(sys.stdin); sys.exit(0 if any(p.get('project_name')=='$AIVEN_PROJECT' for p in d) else 1)" 2>/dev/null; then
  avn project create "$AIVEN_PROJECT" --format json >/dev/null
fi

echo "==> Ensuring free MySQL service: $AIVEN_SERVICE"
if ! avn service list "$AIVEN_PROJECT" --format json | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if any(s.get('service_name')=='$AIVEN_SERVICE' for s in d) else 1)" 2>/dev/null; then
  avn service create mysql "$AIVEN_SERVICE" -t mysql -p free --cloud "$AIVEN_CLOUD" --project "$AIVEN_PROJECT" --format json >/dev/null
  echo "Waiting for MySQL to become RUNNING (2-5 min)..."
  while true; do
    state="$(avn service get "$AIVEN_PROJECT" "$AIVEN_SERVICE" --format json | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")"
    [[ "$state" == "RUNNING" ]] && break
    sleep 15
  done
fi

echo "==> Reading MySQL connection info..."
CONN="$(avn service connection-info "$AIVEN_PROJECT" "$AIVEN_SERVICE" --format json)"
DB_HOST="$(echo "$CONN" | python3 -c "import sys,json; print(json.load(sys.stdin)['host'])")"
DB_PORT="$(echo "$CONN" | python3 -c "import sys,json; print(json.load(sys.stdin)['port'])")"
DB_USER="$(echo "$CONN" | python3 -c "import sys,json; print(json.load(sys.stdin)['user'])")"
DB_PASS="$(echo "$CONN" | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])")"
DB_NAME="$(echo "$CONN" | python3 -c "import sys,json; print(json.load(sys.stdin.get('dbname','defaultdb') or 'defaultdb')")"

CREDS_FILE="$ROOT/deploy/production-credentials.txt"
mkdir -p "$ROOT/deploy"
cat > "$CREDS_FILE" <<EOF
# DriveClear Production — generated $(date -u +"%Y-%m-%dT%H:%M:%SZ")
API_URL=$RENDER_API_URL/api/v1
ALLOWED_HOSTS=driveclear-api.onrender.com

DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS

# Health: curl $RENDER_API_URL/api/v1/health/
EOF
chmod 600 "$CREDS_FILE"

echo "==> Updating Render environment..."
python3 <<PY
import json, yaml, urllib.request

api_key = yaml.safe_load(open("$HOME/.render/cli.yaml"))["api"]["key"]
env = {
    "ALLOWED_HOSTS": "driveclear-api.onrender.com",
    "DB_HOST": "$DB_HOST",
    "DB_PORT": "$DB_PORT",
    "DB_NAME": "$DB_NAME",
    "DB_USER": "$DB_USER",
    "DB_PASSWORD": "$DB_PASS",
    "CORS_ALLOWED_ORIGINS": "http://localhost:3000",
}
payload = [{"key": k, "value": v} for k, v in env.items()]
req = urllib.request.Request(
    "https://api.render.com/v1/services/$RENDER_SERVICE/env-vars",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    method="PUT",
)
with urllib.request.urlopen(req) as resp:
    print("Render env updated:", resp.status)
PY

echo "==> Triggering Render deploy..."
curl -sS -X POST -H "Authorization: Bearer $API_KEY" \
  "https://api.render.com/v1/services/$RENDER_SERVICE/deploys" \
  -H "Content-Type: application/json" \
  -d '{"clearCache":"clear"}' >/dev/null

echo ""
echo "Done. Credentials saved to: deploy/production-credentials.txt"
echo "API: $RENDER_API_URL/api/v1"
echo "Wait ~3 min for deploy, then: curl $RENDER_API_URL/api/v1/health/"
