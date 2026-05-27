#!/usr/bin/env python3
"""Deploy DriveClear free: Aiven MySQL + Render web. Uses Aiven REST API + Render API."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDER_SERVICE = "srv-d86u5gd7vvec73amkjt0"
RENDER_API_URL = "https://driveclearbackend-production.up.railway.app"
AIVEN_PROJECT = os.environ.get("AIVEN_PROJECT", "driveclear")
AIVEN_SERVICE = os.environ.get("AIVEN_SERVICE", "driveclear-mysql")
AIVEN_CLOUD = os.environ.get("AIVEN_CLOUD", "google-asia-southeast1")
AIVEN_API = "https://api.aiven.io/v1"


def load_token() -> str:
    token = os.environ.get("AIVEN_TOKEN", "").strip()
    if token:
        return token
    token_file = ROOT / "deploy" / "aiven.token"
    if token_file.exists():
        return token_file.read_text().strip()
    raise SystemExit(
        "Missing Aiven token. In browser (already logged in):\n"
        "  1. Open https://console.aiven.io/profile/tokens\n"
        "  2. Generate token → copy it\n"
        "  3. Save to deploy/aiven.token  OR  export AIVEN_TOKEN='...'\n"
        "  4. Re-run: ./scripts/deploy-free.sh"
    )


def load_render_key() -> str:
    import yaml

    cfg = yaml.safe_load((Path.home() / ".render" / "cli.yaml").read_text())
    return cfg["api"]["key"]


def aiven(method: str, path: str, token: str, body: dict | None = None) -> dict:
    url = f"{AIVEN_API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"aivenv1 {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise SystemExit(f"Aiven API error {exc.code} {path}: {detail}") from exc


def render_request(method: str, path: str, key: str, body: dict | None = None) -> dict:
    url = f"https://api.render.com/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def ensure_project(token: str) -> None:
    projects = aiven("GET", "/project", token).get("projects", [])
    if any(p.get("project_name") == AIVEN_PROJECT for p in projects):
        print(f"Project exists: {AIVEN_PROJECT}")
        return
    me = aiven("GET", "/me", token)
    accounts = me.get("accounts") or []
    if not accounts:
        raise SystemExit("No Aiven account found on this token.")
    account_id = accounts[0]["account_id"]
    print(f"Creating project: {AIVEN_PROJECT}")
    aiven("POST", "/project", token, {"project": AIVEN_PROJECT, "account_id": account_id})


def ensure_mysql(token: str) -> None:
    services = aiven("GET", f"/project/{AIVEN_PROJECT}/service", token).get("services", [])
    existing = next((s for s in services if s.get("service_name") == AIVEN_SERVICE), None)
    if existing:
        print(f"MySQL exists: {AIVEN_SERVICE} ({existing.get('state')})")
        if existing.get("state") != "RUNNING":
            wait_running(token)
        return

    print(f"Creating free MySQL: {AIVEN_SERVICE} on {AIVEN_CLOUD}")
    aiven(
        "POST",
        f"/project/{AIVEN_PROJECT}/service",
        token,
        {
            "service_type": "mysql",
            "service_name": AIVEN_SERVICE,
            "plan": "free",
            "cloud": AIVEN_CLOUD,
        },
    )
    wait_running(token)


def wait_running(token: str) -> None:
    print("Waiting for MySQL RUNNING (2-5 min)...")
    while True:
        services = aiven("GET", f"/project/{AIVEN_PROJECT}/service", token).get("services", [])
        svc = next((s for s in services if s.get("service_name") == AIVEN_SERVICE), None)
        state = (svc or {}).get("state", "UNKNOWN")
        print(f"  state={state}")
        if state == "RUNNING":
            return
        if state in {"FAILED", "POWEROFF"}:
            raise SystemExit(f"MySQL service failed: {state}")
        time.sleep(15)


def connection_info(token: str) -> dict[str, str]:
    svc = aiven("GET", f"/project/{AIVEN_PROJECT}/service/{AIVEN_SERVICE}", token)["service"]
    params = svc.get("service_uri_params") or {}
    if params:
        return {
            "DB_HOST": params["host"],
            "DB_PORT": str(params["port"]),
            "DB_USER": params["user"],
            "DB_PASSWORD": params["password"],
            "DB_NAME": params.get("dbname", "defaultdb"),
        }

    users = aiven("GET", f"/project/{AIVEN_PROJECT}/service/{AIVEN_SERVICE}/user", token).get("users", [])
    if not users:
        raise SystemExit("Could not read MySQL users from Aiven.")
    user = users[0]
    return {
        "DB_HOST": svc["connection_info"]["mysql"]["host"],
        "DB_PORT": str(svc["connection_info"]["mysql"]["port"]),
        "DB_USER": user["username"],
        "DB_PASSWORD": user["password"],
        "DB_NAME": user.get("database", "defaultdb"),
    }


def update_render(key: str, db: dict[str, str], *, use_sqlite: bool = False) -> None:
    existing = render_request("GET", f"/services/{RENDER_SERVICE}/env-vars", key)
    merged = {item["envVar"]["key"]: item["envVar"].get("value", "") for item in existing}
    merged.update(
        {
            "ALLOWED_HOSTS": "driveclearbackend-production.up.railway.app",
            "CORS_ALLOWED_ORIGINS": merged.get("CORS_ALLOWED_ORIGINS") or "http://localhost:3000",
            "SECURE_SSL_REDIRECT": "false",
            "USE_SQLITE": "false",
        }
    )
    if use_sqlite:
        merged["USE_SQLITE"] = "true"
    else:
        merged.update(db)
        merged["USE_SQLITE"] = "false"
    payload = [{"key": k, "value": v} for k, v in merged.items() if v is not None]
    render_request("PUT", f"/services/{RENDER_SERVICE}/env-vars", key, payload)
    print("Render env vars updated.")
    render_request("POST", f"/services/{RENDER_SERVICE}/deploys", key, {"clearCache": "clear"})
    print("Render deploy triggered.")


def save_credentials(db: dict[str, str]) -> Path:
    out = ROOT / "deploy" / "production-credentials.txt"
    out.parent.mkdir(exist_ok=True)
    lines = [
        "# DriveClear Production credentials",
        f"API_URL={RENDER_API_URL}/api/v1",
        f"ALLOWED_HOSTS=driveclearbackend-production.up.railway.app",
    ]
    lines.extend(f"{k}={v}" for k, v in db.items())
    lines.append(f"# Health: curl {RENDER_API_URL}/api/v1/health/")
    out.write_text("\n".join(lines) + "\n")
    out.chmod(0o600)
    return out


def deploy_sqlite_interim(render_key: str) -> None:
    print("No Aiven token yet — deploying with SQLite (free, interim)...")
    update_render(render_key, {}, use_sqlite=True)
    out = ROOT / "deploy" / "production-credentials.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        "\n".join(
            [
                "# DriveClear — INTERIM SQLite deploy (free Render tier)",
                f"API_URL={RENDER_API_URL}/api/v1",
                "USE_SQLITE=true",
                "NOTE=Replace with Aiven MySQL: save token to deploy/aiven.token and re-run deploy-free.sh",
                f"# Health: curl {RENDER_API_URL}/api/v1/health/",
            ]
        )
        + "\n"
    )
    out.chmod(0o600)
    print(f"Interim credentials: {out}")


def main() -> None:
    render_key = load_render_key()
    token_file = ROOT / "deploy" / "aiven.token"

    if not os.environ.get("AIVEN_TOKEN", "").strip() and not token_file.exists():
        # Try clipboard (user may have copied token from Aiven console)
        try:
            import subprocess

            clip = subprocess.check_output(["pbpaste"], text=True).strip()
            if len(clip) > 20 and " " not in clip and clip not in {"avn user login"}:
                token_file.parent.mkdir(exist_ok=True)
                token_file.write_text(clip)
                token_file.chmod(0o600)
                print("Found token in clipboard → saved to deploy/aiven.token")
        except Exception:
            pass

    try:
        token = load_token()
    except SystemExit:
        deploy_sqlite_interim(render_key)
        raise SystemExit(
            "\nAPI deploying with SQLite. For persistent MySQL:\n"
            "  1. https://console.aiven.io/profile/tokens → Generate token → Copy\n"
            "  2. pbpaste > deploy/aiven.token\n"
            "  3. ./scripts/deploy-free.sh"
        ) from None

    me = aiven("GET", "/me", token)
    print(f"Aiven user: {me.get('user', {}).get('user_email', 'ok')}")

    ensure_project(token)
    ensure_mysql(token)
    db = connection_info(token)
    creds_file = save_credentials(db)
    update_render(render_key, db, use_sqlite=False)

    print("\n=== DEPLOY COMPLETE (MySQL) ===")
    print(f"Credentials: {creds_file}")
    print(f"API: {RENDER_API_URL}/api/v1")
    print("Wait ~3 min, then: curl https://driveclearbackend-production.up.railway.app/api/v1/health/")


if __name__ == "__main__":
    main()
