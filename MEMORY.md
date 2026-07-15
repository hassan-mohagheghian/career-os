# Job Search Memory

## Profile
- **Name:** Hassan Mohagheghian
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

**When working with API:** Use redacted versions from `inputs/redacted/`
**Original files:** NEVER send `inputs/original/` content to any API

### Workflow
**When I (AI) read/process user data via API:** Use `inputs/redacted/` files ONLY
**When generating resumes for user:** Read from `inputs/simplified/` (local, not sent to API)
**Original files:** Never modify files in `inputs/original/`
**Generated resumes:** Store in `resumes/` (not in inputs/)
**Platform display:** data/resumes.json contains real info for user's eyes only
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
│   │   └── jobs.db      # SQLite database
│   ├── client/          # React + Tailwind frontend
│   │   └── src/App.jsx
│   └── start.sh         # Startup script
├── data/                # JSON data files (source of truth for DB)
├── inputs/              # User-provided files
│   ├── original/        # NEVER MODIFY
│   ├── simplified/      # Text-only versions (for local use)
│   └── redacted/        # Personal info replaced (for API calls)
├── resumes/             # Generated resumes (my output)
│   ├── overall.txt      # Improved base resume
│   └── by_job/          # Per-job tailored resumes
├── jobs/                # Individual job analysis files
└── MEMORY.md            # This file
```

## Workflow
1. User submits LinkedIn URL via app (Add Job tab)
2. URL saved to pending_jobs table in SQLite
3. I fetch the job, analyze it, create resume
4. I run process_pending.py to update the database
5. App auto-refreshes with new data

## Adding New Jobs
When user submits a URL:
1. Fetch job from LinkedIn
2. Create job file in `jobs/`
3. Create resume in `resumes/by_job/`
4. Use `app/server/process_pending.py` to:
   - Add to jobs table
   - Add to summaries table
   - Add to resumes table
   - Mark pending as processed
5. Update `data/` JSON files for backup

## Skill Gaps
- **Not learning:** Go
- **Blocked by language:** German C1 (suena energy)
- **Priority to learn:** TypeScript (7/19 jobs)
- **Explore:** Rust (personal project, low market demand)
- **Skip:** C, WASM (zero market demand in current search)
