# Push Backend to GitHub (separate repo)

Use this when the backend lives in its **own GitHub repository**, separate from the frontend.

## 1. Create repo on GitHub

1. Go to https://github.com/new
2. Repository name: `DriveClear_Backend`
3. **Do not** add README, .gitignore, or license (this folder already has them)
4. Create repository

## 2. Push this folder

From inside `DriveClear_Backend`:

```bash
git init
git add .
git commit -m "Initial backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/DriveClear_Backend.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## 3. Connect Render

1. https://dashboard.render.com → **New +** → **Blueprint**
2. Connect GitHub → select **DriveClear_Backend** repo
3. **Root Directory**: leave **empty** (repo root is the backend)
4. Render reads `render.yaml` in this folder
5. Deploy

See [DEPLOY.md](./DEPLOY.md) for environment variables.

## 4. Local workspace (optional)

For local dev with frontend, clone both repos as siblings:

```
your-workspace/
├── DriveClear_Backend/    ← this repo
└── DriveClear_Frontend/   ← frontend repo
```

Then run `./scripts/dev-full-stack.sh` from the backend folder.
