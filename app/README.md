# Job Search App

SQLite + Flask + React + Tailwind

## Setup

### 1. Initialize database
```bash
cd server
python db.py
```

### 2. Start Flask server
```bash
cd server
pip install -r requirements.txt
python app.py
```

### 3. Start React dev server
```bash
cd client
npm install
npm run dev
```

### 4. Build for production
```bash
cd client
npm run build
# Flask serves from client/dist/
```

## API Endpoints

- `GET /api/all` — All data in one response
- `GET /api/stream/all` — Streaming version
- `GET /api/jobs` — Jobs only
- `GET /api/jobs/<num>` — Single job
- `GET /api/summaries` — Summaries
- `GET /api/resumes` — Resumes
- `GET /api/tech-learning` — Tech learning
- `GET /api/tech-stack` — Tech stack
- `GET /api/cities` — Cities

## Streaming

For API calls, use `/api/stream/all` which sends data incrementally.
For single requests, use `/api/all` which returns everything at once.
