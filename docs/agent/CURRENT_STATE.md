# Current State

## Environment

- **Python env:** Uses `uv` with `.venv` in root folder
- **Resume/LinkedIn data:** Stored in DB `resumes` table (raw_text column)
- **PII masking:** Applied before sending to any external API

## Privacy Rules

**NEVER send personal info to server/API.** This includes:

- Full name
- Email address
- Phone number
- Company names (current/former employers)
- University names
- Any identifying information

**All personal data (resume, LinkedIn) is stored in the DB `resumes` table.**

## Scoring Rules

**Allow same scores.** 92.5 and 92.2 both round to 92. Don't force unique scores. Scores are rounded to nearest integer.
