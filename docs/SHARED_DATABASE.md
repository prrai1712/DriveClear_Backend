# Use the same database locally and on Render

You can run Django on your Mac but connect to **Render’s MySQL** so local dev and production share one database.

## 1. Get the connection string from Render

1. [Render Dashboard](https://dashboard.render.com) → your **MySQL** service (`driveclear-mysql`)
2. **Connect** → copy **External Database URL**  
   (not the internal URL — that only works inside Render)
3. It looks like:
   `mysql://driveclear:xxxxxxxx@dpg-xxxxx-a.oregon-postgres.render.com:3306/driveclear`  
   (host/port vary; Render MySQL uses port **3306**)

## 2. Configure local backend

Edit `DriveClear_Backend/.env`:

```env
# Comment out local DB_* when using Render (DATABASE_URL wins)
# DB_HOST=127.0.0.1
# ...

DATABASE_URL=mysql://USER:PASSWORD@HOST:3306/DATABASE
```

Restart Django:

```bash
cd backend
.venv/bin/python manage.py runserver
```

Check:

```bash
.venv/bin/python manage.py dbshell
# or
curl http://127.0.0.1:8000/api/v1/health/
```

`database: true` means the remote DB is reachable.

**Frontend** stays local (`npm run dev`); only `NEXT_PUBLIC_API_URL` must point to your API (`http://127.0.0.1:8000/api/v1` for local backend, or Render URL if you test against deployed API).

## 3. DataGrip — same database

Parse the URL:

| URL part | DataGrip field |
|----------|----------------|
| `USER` | User |
| `PASSWORD` | Password |
| `HOST` | Host |
| `3306` | Port |
| `DATABASE` | Database |

**Test Connection** → same tables as production.

SSL: if connection fails, in DataGrip → **Advanced** → try `useSSL=true` or add `?ssl-mode=REQUIRED` to the URL (depends on Render MySQL settings).

## 4. Migrations

Run once against the shared DB (from your Mac):

```bash
cd backend
.venv/bin/python manage.py migrate
```

Render’s start command also runs `migrate` on deploy — avoid conflicting migrations from two places at once.

## Warnings

- **Local actions write to production data** (users, challans, payments, fulfilment).
- Use **Razorpay test keys** locally unless you intend real charges.
- Prefer a **staging** Render database for daily dev; use prod DB only when you really need identical data.
- Never commit `DATABASE_URL` (it contains the password) — `.env` is gitignored.

## Switch back to local-only MySQL

Remove or comment `DATABASE_URL` in `.env`, restore `DB_*` lines, restart Django.
