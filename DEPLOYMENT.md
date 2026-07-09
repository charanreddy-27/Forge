# Deploying Forge

Forge has two halves with very different hosting needs:

| Part | What it is | Where it runs |
|---|---|---|
| **Dashboard + marketing site** | Next.js 14 app (`dashboard/`) | **Vercel** ✅ |
| **Agent layer + engine** | FastAPI, Postgres, Redis, n8n, workers | A server / container host ❌ *(not Vercel)* |

Vercel is serverless — it can't run persistent Postgres/Redis/n8n or long-lived worker
processes. So the play is: **deploy the Next.js app to Vercel in demo mode** (fully explorable
on seeded data, zero infrastructure), and optionally point it at a self-hosted agent layer
later by setting one environment variable.

---

## Part 1 — Ship the dashboard to Vercel (5 minutes)

### 1. Push the repo to GitHub

```bash
git add .
git commit -m "feat: portfolio site + demo mode"
git push
```

### 2. Import the project on Vercel

1. Go to [vercel.com/new](https://vercel.com/new) and import your GitHub repo.
2. **Set the Root Directory to `dashboard`.** This is the one setting that matters — the Next.js
   app lives in the `dashboard/` subfolder, not the repo root.
   *(Project → Settings → General → Root Directory → `dashboard`.)*
3. Framework preset: **Next.js** (auto-detected). Leave build/output settings at their defaults:
   - Build command: `next build` (default)
   - Output directory: `.next` (default)
   - Install command: `npm install` (default)

### 3. Environment variables — none required

**Demo mode is the zero-config default.** With no variables set, the whole dashboard runs on
seeded data and the chat box / incident actions simulate the agent client-side. Just deploy.

Optional, in **Project → Settings → Environment Variables**:

| Name | Value | Why |
|---|---|---|
| `NEXT_PUBLIC_SITE_URL` | `https://<your-domain>` | Makes OG/Twitter card URLs absolute (nice for sharing). |

> Leave `FORGE_API_URL` **unset** — its absence is what keeps the app in demo mode. Setting it
> is how you later switch to a real backend.

### 4. Deploy

Click **Deploy**. Vercel builds and gives you a `*.vercel.app` URL. Open it — the landing page,
About pages, and a fully clickable demo dashboard are live.

### 5. (Optional) Custom domain

Project → Settings → Domains → add your domain and follow the DNS instructions (a `CNAME` to
`cname.vercel-dns.com`, or Vercel's nameservers). Then update `NEXT_PUBLIC_SITE_URL` to match.

---

## Part 2 — (Optional) Connect a real backend later

If you host the agent layer somewhere that can run containers (Railway, Render, Fly.io, a VPS
with `docker compose up`), wire the dashboard to it:

1. Deploy the platform on that host (`docker compose up -d`) and expose the agent layer
   (port 8000) over HTTPS.
2. In Vercel, set `FORGE_API_URL=https://<your-agent-layer-host>` and **remove**
   `NEXT_PUBLIC_FORGE_DEMO`.
3. Redeploy. The dashboard now reads live workflows, runs, incidents, and costs.

---

## Local sanity check before you deploy

```bash
cd dashboard
npm install
npm run build      # must pass clean
npm run start      # open http://localhost:3000 — runs in demo mode
```

---

## ✅ Manual checklist — the things only you can do

- [ ] **Push** the repo to GitHub.
- [ ] **Import** it on Vercel and set **Root Directory = `dashboard`**.
- [ ] (Optional) add `NEXT_PUBLIC_SITE_URL=<domain>` for absolute OG links. No env vars are
      required for the demo to work.
- [ ] **Deploy** and confirm the live URL works (landing + demo dashboard).
- [ ] **Custom domain** (optional): add it in Vercel and point DNS.
- [ ] **Screenshots:** drop real captures into `docs/screenshots/` (`overview.png`,
      `incidents.png`, `workflow-detail.png`, `costs.png`) so the README renders images.
- [ ] **Repo URL:** update `dashboard/lib/profile.ts` → `repo` and the README links once the
      repo's public URL is final.
- [ ] **LinkedIn post:** write the launch post, then replace the placeholder LinkedIn link on
      the About-the-Project page (`app/(marketing)/about-project/page.tsx`) with the post URL.
- [ ] **Verify OG card:** paste the deployed URL into the
      [OpenGraph debugger](https://www.opengraph.xyz) and confirm the image renders.
