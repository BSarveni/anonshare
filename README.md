# AnonShare

Anonymous image sharing with group chat, AI content moderation, and anomaly detection.

## Deploy to Railway

1. Push this repo to GitHub.

2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.

3. Railway auto-detects the repo. Create these services manually (5 total — Railway’s per-project limit):

   - **PostgreSQL** plugin (click Add Plugin)
   - **Redis** plugin (click Add Plugin)
   - Service from `/backend` (set root dir to `/backend`, `Dockerfile`)
   - Service from `/backend` with `Dockerfile.celery-combined` (rename to `celery` — worker + beat in one container)
   - Service from `/frontend` (set root dir to `/frontend`, `Dockerfile`)

   Do **not** add separate `Dockerfile.celery` and `Dockerfile.beat` services unless your plan allows more than 5 services. For local dev you can still run worker and beat in separate terminals (see below).

4. For **api** and **celery**, go to **Variables** → add all vars from `backend/.env.example`, and reference `DATABASE_URL` / `REDIS_URL` from the plugins.

5. For the **frontend** service, add:

   - `VITE_API_URL` — copy the backend service's public URL from the Railway dashboard
   - `VITE_WS_URL` — same URL but replace `https://` with `wss://`

6. Deploy. Visit the frontend service URL.

**Networking ports:** The API listens on Railway's `PORT` variable (often not 8000). In **api** → **Settings** → **Networking**, set the public domain target port to the value of `PORT` in that service's variables (or redeploy after the latest `Dockerfile`, which uses `${PORT:-8000}`). Frontend target port is **3000**.

The API container runs `prestart.sh` before Uvicorn (`alembic upgrade head`, then `python init_db.py`). Railway's `postgresql://` URLs are rewritten to `postgresql+asyncpg://` automatically in `database.py`.

## Local dev

Start Postgres and Redis only (run backend and frontend on the host with hot reload):

```bash
docker compose -f docker-compose.dev.yml up
```

**Backend** (separate terminal):

```bash
cd backend
cp .env.example .env   # set DATABASE_URL, REDIS_URL, SECRET_KEY, ALLOWED_ORIGINS=http://localhost:5173
pip install -r requirements.txt
alembic upgrade head
python init_db.py
uvicorn main:app --reload
```

Optional Celery (separate terminals):

```bash
celery -A tasks.celery_app worker --loglevel=info
celery -A tasks.celery_app beat --loglevel=info
```

**Frontend**:

```bash
cd frontend
cp .env.example .env   # VITE_API_URL=http://localhost:8000, VITE_WS_URL=ws://localhost:8000
npm install
npm run dev
```

- API docs: http://localhost:8000/docs  
- App: http://localhost:5173
