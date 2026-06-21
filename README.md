# Passport Social Media Monitoring & Intelligence Platform

Backend-first MVP for monitoring passport-related discussions from Reddit and YouTube, processing them with Groq NLP, generating sentence-transformer embeddings, clustering similar discussions, and presenting insights through a React dashboard.

## Architecture

```text
Reddit + YouTube
  -> FastAPI ingestion services
  -> PostgreSQL posts
  -> Groq analysis
  -> SentenceTransformer embeddings
  -> Semantic clustering
  -> FastAPI APIs
  -> React dashboard
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000/api/v1
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

## Environment Variables

Backend:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/passport_monitor
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=passport-monitor:v1.0

YOUTUBE_API_KEY=
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

SCHEDULER_ENABLED=false
PIPELINE_INTERVAL_MINUTES=180
REDDIT_LIMIT_PER_KEYWORD=20
YOUTUBE_MAX_RESULTS_PER_KEYWORD=20
ANALYSIS_BATCH_SIZE=50
EMBEDDING_BATCH_SIZE=100
```

Frontend:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## API Endpoints

```text
GET /api/v1/health
GET /api/v1/posts
GET /api/v1/posts/{id}
GET /api/v1/clusters
GET /api/v1/clusters/{id}
GET /api/v1/clusters/{id}/posts
GET /api/v1/analytics
GET /api/v1/search
```

## Scheduler

The scheduler runs this pipeline:

```text
Reddit ingestion
-> YouTube ingestion
-> Groq analysis
-> Embeddings
-> Clustering
```

Enable it with:

```env
SCHEDULER_ENABLED=true
```

Each stage is isolated. If one stage fails, the scheduler logs the error and continues to the next stage.

## Neon PostgreSQL

1. Create a Neon project.
2. Create a database named `passport_monitor`.
3. Enable the `vector` extension from the SQL editor:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

4. Copy the pooled PostgreSQL connection string.
5. Use the SQLAlchemy psycopg format:

```text
postgresql+psycopg://USER:PASSWORD@HOST/passport_monitor?sslmode=require
```

## Render Deployment

Use the included `render.yaml`.

Production startup command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these Render environment variables:

```text
DATABASE_URL
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
YOUTUBE_API_KEY
GROQ_API_KEY
CORS_ORIGINS
SCHEDULER_ENABLED=true
```

## Vercel Deployment

Deploy the `frontend` directory to Vercel.

Set:

```text
VITE_API_BASE_URL=https://your-render-api.onrender.com/api/v1
```

The included `frontend/vercel.json` handles SPA routing.

## MVP Scope

Implemented:

- PostgreSQL + SQLAlchemy models
- Reddit ingestion
- YouTube ingestion
- Groq NLP analysis
- SentenceTransformer embeddings
- Semantic clustering
- FastAPI APIs
- React dashboard, clusters, and search pages
- APScheduler orchestration
- Render/Vercel deployment config

Not included:

- Authentication
- Multi-tenant support
- Scrapling-based platforms
- Enterprise audit or billing features
