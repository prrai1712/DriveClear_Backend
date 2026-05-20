# DriveClear deployment

| Repo | Deploy |
|------|--------|
| **DriveClear_Backend** (this repo) | [Render](https://render.com) — [DEPLOY.md](../DEPLOY.md) |
| **DriveClear_Frontend** | [Vercel](https://vercel.com) — separate GitHub repo |

## Order

1. Push **DriveClear_Backend** to GitHub → deploy on Render
2. Push **DriveClear_Frontend** to GitHub → deploy on Vercel
3. Set Render `CORS_ALLOWED_ORIGINS` = Vercel URL
4. Add Vercel domain in Firebase authorized domains

See [GITHUB.md](../GITHUB.md) for pushing this repo to GitHub.
