# DriveClear Backend

Standalone Django REST API — **its own GitHub repo**, deployed to **Render**.

Frontend repo: [DriveClear_Frontend](https://github.com/prrai1712/DriveClear_Frontend) (Vercel).

## GitHub (separate repo)

This folder is the **backend repository root**. Push it to its own GitHub repo:

```bash
cd DriveClear_Backend
git init
git add .
git commit -m "Initial backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/DriveClear_Backend.git
git push -u origin main
```

See [GITHUB.md](./GITHUB.md) for full steps.

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./scripts/setup_mysql.sh   # after init_mysql_local.sql in DataGrip
python manage.py runserver
```

API: http://localhost:8000/api/v1/health/

## Deploy on Render

See [DEPLOY.md](./DEPLOY.md) — connect **this repo** directly (no Root Directory needed).

## Run backend + frontend locally

If `DriveClear_Frontend` is cloned as a sibling folder:

```bash
./scripts/dev-full-stack.sh
```
