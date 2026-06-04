# BusinessOS Backend

FastAPI backend for the BusinessOS CRM and HRM modules.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `.env`:

```env
DATABASE_URL=postgresql://postgres:NewStrongPass123@localhost:5432/business_os
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SQL_ECHO=false
```

Create database schemas and tables:

```powershell
python -m backend.core.create_tables
```

Run the API:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open API docs at `http://127.0.0.1:8000/docs`.

The API exposes both direct backend paths such as `/crm/leads` and frontend-friendly
aliases such as `/api/crm/leads`, matching `NEXT_PUBLIC_API_URL` usage in `src`.
Auth endpoints for the current frontend are available at `/api/auth/login` and
`/api/auth/me`.
