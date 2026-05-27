# Deploy DriveClear Backend on Railway

This is a **standalone backend GitHub repo**. Connect it directly to Railway.

Deploy frontend first repo setup: [DriveClear_Frontend](https://github.com/prrai1712/DriveClear_Frontend)

---

## Step 1 — Push to GitHub

See [GITHUB.md](./GITHUB.md) if not pushed yet.

---

## Step 2 — Create Railway service

1. https://railway.app → **New Project**
2. Connect GitHub → select **DriveClear_Backend** repo
3. Railway automatically builds and deploys the service.

---

Railway → **Environment Variables**:

| Variable | Value |
|----------|--------|
| `ALLOWED_HOSTS` | `driveclearbackend-production.up.railway.app` (your hostname) |
| `CORS_ALLOWED_ORIGINS` | `https://YOUR-APP.vercel.app` (after Vercel deploy) |
| `FIREBASE_PROJECT_ID` | `driveclear-82af6` |
| `FIREBASE_CREDENTIALS_JSON` | Firebase service account JSON (one line) |
| `SMS_PROVIDER` | `msg91` or `mock` |
| `MSG91_AUTH_KEY` | From msg91.com |
| `RAZORPAY_KEY_ID` / `KEY_SECRET` / `WEBHOOK_SECRET` | Razorpay keys |
| `EXTERNAL_CHALLAN_API_URL` | See `.env.example` |
| `EXTERNAL_CHALLAN_FIND_URL` | See `.env.example` |
| `API_PAYLOAD_ENCRYPTION_ENABLED` | `true` |
| `API_PAYLOAD_ENCRYPTION_KEY` | Same key as frontend |

Generate encryption key:

```bash
python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

---

## Step 4 — Verify

```bash
curl https://YOUR-SERVICE.up.railway.app/api/v1/health/
```

Save API URL for frontend:

```
https://YOUR-SERVICE.up.railway.app/api/v1
```

---

## Step 5 — After Vercel deploy

1. Update `CORS_ALLOWED_ORIGINS` with Vercel URL → redeploy
2. Firebase → Authorized domains → add Vercel domain
