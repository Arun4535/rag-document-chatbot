# Deploy DocSense on Render

## 1. Push to GitHub

```bash
git add .
git commit -m "production architecture"
git push origin main
```

## 2. Create Render Blueprint

1. Go to Render.
2. Click **New**.
3. Choose **Blueprint**.
4. Connect the GitHub repository.
5. Select the repo containing `render.yaml`.
6. Render creates:
   - `docsense-frontend`
   - `docsense-backend`
   - `docsense-db`

## 3. Set Environment Variables

Set these on the backend service:

```text
ANTHROPIC_API_KEY=your_anthropic_key
VOYAGE_API_KEY=your_voyage_key
```

`DATABASE_URL` is injected automatically from the managed PostgreSQL service.

## 4. Deploy

Trigger deploys for the backend and frontend services.

The frontend URL will look like:

```text
https://docsense-frontend.onrender.com
```

Add that URL to your resume, LinkedIn Featured section, and GitHub README.

## Local Docker Test

```bash
cp .env.example .env
# edit .env and add ANTHROPIC_API_KEY, VOYAGE_API_KEY, POSTGRES_PASSWORD
docker compose up --build
```

Open:

```text
http://localhost
```
