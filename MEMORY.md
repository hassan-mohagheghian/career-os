w# Job Search Memory

## Profile

- **Role:** Senior Software Engineer (9+ years)
- **Location:** Isfahan, Iran → targeting Berlin, Germany
- **Core Stack:** Python (Django, FastAPI, DRF), PostgreSQL, Docker/K8s, AWS/GCP, Terraform, Linux
- **Secondary:** Rust (Axum, Tokio), TypeScript, React, Next.js
- **AI:** M.Sc. AI, LangChain, LlamaIndex, Autogen
- **Architecture:** Microservices, TDD, DDD, Clean Architecture, Hexagonal, CQRS
- **Open-source:** WorkGraph, RustWatch, Order Management DDD, User Management DDD
- **Languages:** English B2 (self-learning, no professional use), German A1 (learning A2), Persian Native

## Constraints

### Language Preference

**Use:** Python, Rust, TypeScript, C, WASM
**Do NOT learn:** Go or other languages right now

### Visa & Relocation

**Need:** Visa sponsorship for Germany + relocation from Iran
**Strategy:** Apply to companies with visa capability. Remote-first roles allow working from Iran initially.

## CRITICAL RULES

### PRIVACY — SEVERE

**NEVER send personal info to server/API.** This includes:

- Full name
- Email address
- Phone number
- Company names (current/former employers)
- University names
- Any identifying information

**All personal data (resume, LinkedIn) is stored in the DB `resumes` table.** PII is masked before any external API calls.

### Workflow

**Resume/LinkedIn data:** Stored in DB `resumes` table (raw_text column)
**PII masking:** Applied before sending to any external API
**Python env:** User uses `uv` with `.venv` in root folder

### Scoring

**Allow same scores.** 92.5 and 92.2 both round to 92. Don't force unique scores. Scores are rounded to nearest integer.

## Project Structure

```
Job-Search/
├── app/                 # Main application (SQLite + Flask + React + Tailwind)
│   ├── server/          # Flask API + SQLite database
│   │   ├── app.py       # Flask server with streaming support
│   │   ├── db.py        # Database initialization
│   │   └── db/jobs.db   # SQLite database
│   ├── client/          # React + Tailwind frontend
│   │   └── src/App.jsx
│   └── start.sh         # Startup script
├── .env                 # Environment config (DB_PATH, TEMP_DIR, etc.)
└── MEMORY.md            # This file
```

## Workflow

1. User submits LinkedIn URL via app (Add Job tab)
2. URL saved to pending_jobs table in SQLite
3. Worker fetches the job, analyzes it, scores it
4. All results saved to DB (jobs, summaries, resumes tables)
5. App auto-refreshes with new data
6. Tmp files cleaned up after processing completes

## Skill Gaps

- **Not learning:** Go
- **Blocked by language:** German C1 (suena energy)
- **Priority to learn:** TypeScript (7/19 jobs)
- **Explore:** Rust (personal project, low market demand)
- **Skip:** C, WASM (zero market demand in current search)
