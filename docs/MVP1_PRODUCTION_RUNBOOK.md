# BusinessOS + Lunexao MVP1 Production Runbook

This is the final wiring checklist for MVP1.

## Production Domains

Use this structure:

```text
lunexao.com              Public Lunexao website
www.lunexao.com          Public Lunexao website
app.lunexao.com          BusinessOS frontend
api.lunexao.com          BusinessOS backend API
```

Temporary URLs can remain active during testing:

```text
https://business-os-edf.pages.dev
https://lunexao-api.onrender.com
```

## 1. Public Website Deployment

Cloudflare Pages project: `lunexao-website`

Settings:

```text
Repository: PVJumav/business_os
Branch: main
Root directory: lunexao-website
Framework preset: None / Static
Build command: leave empty
Build output directory: .
```

Custom domains:

```text
lunexao.com
www.lunexao.com
```

The website inquiry and job application links currently open email to:

```text
pauljumav@gmail.com
```

## 2. BusinessOS Frontend Deployment

Cloudflare Pages project: `business-os`

Settings:

```text
Repository: PVJumav/business_os
Branch: main
Root directory: leave empty
Framework preset: Next.js
Build command: npx @cloudflare/next-on-pages@1
Build output directory: .vercel/output/static
Compatibility flag: nodejs_compat
```

Environment variables:

```text
NEXT_PUBLIC_API_URL=https://api.lunexao.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<google-client-id>
NEXT_PUBLIC_GITHUB_CLIENT_ID=<github-client-id>
```

Custom domain:

```text
app.lunexao.com
```

## 3. Backend API Deployment

Render service: `business-os-api`

Root directory:

```text
backend
```

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
PYTHONPATH="$(pwd):$(dirname "$(pwd)")" python -m backend.core.create_tables && PYTHONPATH="$(pwd):$(dirname "$(pwd)")" uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Production environment variables:

```text
DATABASE_URL=<neon-postgres-url-with-sslmode-require>
SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=https://app.lunexao.com,https://business-os-edf.pages.dev
GOOGLE_CLIENT_ID=<google-client-id>
GITHUB_CLIENT_ID=<github-client-id>
GITHUB_CLIENT_SECRET=<github-client-secret>
SQL_ECHO=false
DB_POOL_RECYCLE_SECONDS=300
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT_SECONDS=30
```

Custom domain:

```text
api.lunexao.com
```

Health checks:

```text
https://api.lunexao.com/
https://api.lunexao.com/api/health
```

## 4. Neon Database

Database must use SSL.

Required connection string shape:

```text
postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

The backend creates tables on startup through:

```bash
python -m backend.core.create_tables
```

After MVP launch:

1. Rotate the Neon password if it was shared in chat or logs.
2. Update Render `DATABASE_URL`.
3. Redeploy backend.

## 5. Email Routing to Gmail

Goal:

```text
info@lunexao.com      -> pauljumav@gmail.com
careers@lunexao.com   -> pauljumav@gmail.com
training@lunexao.com  -> pauljumav@gmail.com
support@lunexao.com   -> pauljumav@gmail.com
```

Cloudflare setup:

1. Open Cloudflare Dashboard.
2. Select `lunexao.com`.
3. Go to Email > Email Routing.
4. Enable Email Routing.
5. Add destination:

```text
pauljumav@gmail.com
```

6. Verify the Gmail confirmation email.
7. Create custom addresses:

```text
info@lunexao.com
careers@lunexao.com
training@lunexao.com
support@lunexao.com
admin@lunexao.com
```

8. Cloudflare should add MX/TXT records automatically if DNS is managed there.

Minimum DNS records for Cloudflare Email Routing:

```text
MX    lunexao.com    route1.mx.cloudflare.net    priority 5
MX    lunexao.com    route2.mx.cloudflare.net    priority 10
MX    lunexao.com    route3.mx.cloudflare.net    priority 20
TXT   lunexao.com    v=spf1 include:_spf.mx.cloudflare.net ~all
```

Recommended DMARC:

```text
TXT   _dmarc.lunexao.com   v=DMARC1; p=none; rua=mailto:pauljumav@gmail.com
```

## 6. OAuth Settings

Google OAuth authorized JavaScript origins:

```text
https://app.lunexao.com
https://business-os-edf.pages.dev
```

GitHub OAuth callback URLs:

```text
https://app.lunexao.com/login
https://business-os-edf.pages.dev/login
```

## 7. MVP1 Acceptance Checklist

Public website:

- `lunexao.com` loads.
- `www.lunexao.com` loads.
- Contact form opens Gmail draft to `pauljumav@gmail.com`.
- Job apply buttons open Gmail draft to `pauljumav@gmail.com`.
- Blog search works.
- Job filter works.

BusinessOS:

- `app.lunexao.com/login` loads.
- User can create account.
- Signup does not auto-login.
- User can sign in with username/password.
- Google sign-in works if configured.
- GitHub sign-in works if configured.
- Dashboard loads.
- CRM list page reads data.
- CRM create form writes data.
- HRM employee page reads data.
- Finance dashboard reads data.
- File upload works where configured.

Backend:

- `api.lunexao.com/` returns API running message.
- `api.lunexao.com/api/health` returns success.
- Render logs show no stale SSL connection errors.
- Neon tables exist.
- Database requests remain stable after backend idle periods.

## 8. Operational Notes

- Render free tier may sleep. For a smoother user experience, use an always-on Render plan.
- Keep the public website and BusinessOS app as separate Cloudflare Pages projects.
- Keep `lunexao.com` for marketing and `app.lunexao.com` for the system.
- Do not expose Neon credentials publicly.
