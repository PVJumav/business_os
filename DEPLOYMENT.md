# BusinessOS Version 5.5 Deployment

This project can be hosted today using:

- Frontend: Cloudflare Pages or Vercel
- Backend API: Render Web Service
- Database: Render PostgreSQL or Neon PostgreSQL

## 1. Backend Environment Variables

Set these in the backend hosting service:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=https://your-cloudflare-pages-domain.pages.dev,http://localhost:3000
SQL_ECHO=false
```

The backend will not start without `DATABASE_URL`. If you deploy using `render.yaml` as a Render Blueprint, the included `business-os-db` database is wired into `DATABASE_URL` automatically. If you create the backend service manually, copy the managed PostgreSQL connection string into the service environment variables yourself.

Backend start command:

```bash
python -m backend.core.create_tables && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## 2. Frontend Environment Variables

Set this in Cloudflare Pages or Vercel:

```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.onrender.com
```

For Cloudflare Pages, also configure:

```text
Build command: npx @cloudflare/next-on-pages@1
Build output directory: .vercel/output/static
Compatibility flag: nodejs_compat
```

Frontend build command:

```bash
npm run build
```

Frontend start command:

```bash
npm run start
```

## 3. Local Run Commands

Backend:

```powershell
cd "C:\Users\PaulJuma\Downloads\Project Orion\business-os-version-5.5"
..\business-os-completed\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd "C:\Users\PaulJuma\Downloads\Project Orion\business-os-version-5.5"
npm run dev
```

Open:

```text
http://localhost:3000/hrm
```

## 4. Deployment Notes

- Do not deploy the local `.env` file because it contains local database credentials.
- Use a managed PostgreSQL connection string for `DATABASE_URL`.
- Update `CORS_ORIGINS` after Cloudflare or Vercel gives you the frontend URL.
- Update `NEXT_PUBLIC_API_URL` after Render gives you the backend URL.
- Run the backend first so the database tables are created before testing the frontend.
