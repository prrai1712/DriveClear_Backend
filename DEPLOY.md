# Deploy DriveClear Backend on Render

This is a **standalone backend GitHub repo**. Connect it directly to Render — **no Root Directory** setting.

Deploy frontend first repo setup: [DriveClear_Frontend](https://github.com/prrai1712/DriveClear_Frontend)

---

## Step 1 — Push to GitHub

See [GITHUB.md](./GITHUB.md) if not pushed yet.

---

## Step 2 — Create Render service (Blueprint)

1. https://dashboard.render.com → **New +** → **Blueprint**
2. Connect GitHub → select **DriveClear_Backend** repo
3. **Root Directory**: leave **empty**
4. Render reads `render.yaml` → creates **driveclear-mysql** + **driveclear-api**
5. Deploy and wait for **Live**

---

## Step 3 — Environment variables

Render → **driveclear-api** → **Environment**:

| Variable | Value |
|----------|--------|
| `ALLOWED_HOSTS` | `driveclear-api.onrender.com` (your hostname) |
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
curl https://YOUR-SERVICE.onrender.com/api/v1/health/
```

Save API URL for frontend:

```
https://YOUR-SERVICE.onrender.com/api/v1
```

---

## Step 5 — After Vercel deploy

1. Update `CORS_ALLOWED_ORIGINS` with Vercel URL → redeploy
2. Firebase → Authorized domains → add Vercel domain
