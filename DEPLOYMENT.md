# BusinessOS Version 5.2 Deployment

This project can be hosted today using:

- Frontend: Vercel
- Backend API: Render Web Service
- Database: Render PostgreSQL or Neon PostgreSQL

## 1. Backend Environment Variables

Set these in the backend hosting service:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
SQL_ECHO=false
```

Backend start command:

```bash
python -m backend.core.create_tables && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## 2. Frontend Environment Variables

Set this in Vercel:

```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.onrender.com
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
cd "C:\Users\PaulJuma\Downloads\Project Orion\business-os-version-5.2"
..\business-os-completed\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd "C:\Users\PaulJuma\Downloads\Project Orion\business-os-version-5.2"
npm run dev
```

Open:

```text
http://localhost:3000/hrm
```

## 4. Deployment Notes

- Do not deploy the local `.env` file because it contains local database credentials.
- Use a managed PostgreSQL connection string for `DATABASE_URL`.
- Update `CORS_ORIGINS` after Vercel gives you the frontend URL.
- Update `NEXT_PUBLIC_API_URL` after Render gives you the backend URL.
- Run the backend first so the database tables are created before testing the frontend.
