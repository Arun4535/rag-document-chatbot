# Deploy DocSense on Render Without Docker

DocSense deploys as one native Python web service on Render. FastAPI serves both:

- `/api/*` backend routes
- the static HTML/CSS/JS frontend

Render also creates a managed PostgreSQL database and attaches a persistent disk for ChromaDB.

## 1. Push to GitHub

```bash
git add .
git commit -m "native render deployment"
git push origin main
```

## 2. Create Render Blueprint

1. Go to Render.
2. Click **New**.
3. Choose **Blueprint**.
4. Connect the GitHub repository.
5. Select the repo containing `render.yaml`.
6. Render creates:
   - `docsense` Python web service
   - `docsense-db` managed PostgreSQL database
   - a persistent disk mounted for ChromaDB

## 3. Set Environment Variables

Set these on the `docsense` web service:

```text
ANTHROPIC_API_KEY=your_anthropic_key
VOYAGE_API_KEY=your_voyage_key
```

`DATABASE_URL` is injected automatically from Render PostgreSQL.

## 4. Deploy

Render uses:

```bash
pip install -r backend/requirements.txt
```

and starts the app with:

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Your live app URL will look like:

```text
https://docsense.onrender.com
```

## Local Run Without Docker

```bash
cp .env.example .env
# edit .env and add ANTHROPIC_API_KEY and VOYAGE_API_KEY
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Local development uses SQLite by default. Render uses PostgreSQL through `DATABASE_URL`.
