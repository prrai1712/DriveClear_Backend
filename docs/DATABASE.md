# Database — MySQL only (Homebrew, no Docker)

## DataGrip — use this connection (ready on your Mac)

Database and tables are already created. Fill exactly:

| Field | Value |
|--------|--------|
| Host | `127.0.0.1` |
| Port | `3306` |
| Database | `driveclear` |
| User | `driveclear` |
| Password | `driveclear` |

Click **Download** driver if prompted → **Test Connection** → **OK** → expand **tables**.

## Optional — root access (admin only)

Local root was reset for development:

| User | Password |
|------|----------|
| `root` | `driveclear_root` |

Use only for admin tasks in DataGrip, not in the Django app.

## If setting up on another machine

Run as root once: `scripts/init_mysql_local.sql`, then `./scripts/setup_mysql.sh`.

## Step 3 — (legacy) DataGrip daily use

Add a **new** data source (or edit the existing one):

| Field | Value |
|--------|--------|
| Name | `driveclear` |
| Host | `127.0.0.1` |
| Port | `3306` |
| Database | `driveclear` |
| User | `driveclear` |
| Password | `driveclear` |

**Test Connection** → expand **driveclear** → **tables**.

## Step 4 — Django migrations

```bash
cd backend
chmod +x scripts/setup_mysql.sh
./scripts/setup_mysql.sh
```

## Step 5 — Run API

```bash
.venv/bin/python manage.py runserver
```

Health: http://127.0.0.1:8000/api/v1/health/ → `"database": true`

## Tables (after migrate)

`users`, `vehicles`, `challan_details`, `challan_fulfilment`, `orders`, `payments`, `django_migrations`, …

## Production (Render)

Uses `DATABASE_URL` from Render MySQL — not your local Homebrew instance.
