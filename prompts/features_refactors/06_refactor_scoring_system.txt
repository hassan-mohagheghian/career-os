Refactor the job scoring system to calculate and store three independent scores during job processing.

Important:
All scores must be calculated based on the existing scoring rules.
Do not create a separate scoring logic.
Each score should aggregate only the relevant rules assigned to that category.

==================================================
1. Fit Score (0-100)
==================================================

Purpose:
Measure how well the job matches the candidate's technical background.

Calculate this score only from Fit Rules.

Consider:
- Python backend alignment
- Role alignment
- Technology overlap
- Seniority level
- Backend engineering experience
- Distributed systems and infrastructure experience

Strong positive signals:
- Python as the primary language
- Django, FastAPI, Flask
- SQLAlchemy, Celery, asyncio
- PostgreSQL, Redis, Kafka
- Backend systems
- APIs
- Microservices
- Cloud-native backend systems

Important:
Ignore:
- Location
- Visa sponsorship
- Competition
- Hiring probability
- Company hiring signals


==================================================
2. Success Score (0-100)
==================================================

Purpose:
Measure the probability of successfully getting the job.

Calculate this score only from Success Rules.

Consider:
- Visa sponsorship availability
- Location suitability
- Language requirements
- Competition level
- Job freshness
- Company hiring signals
- Remote/hybrid possibilities

Important:
Ignore:
- Technical stack matching
- Programming languages
- Backend experience


==================================================
3. Overall Score (0-100)
==================================================

Calculate this score during the same job processing step.

Do not calculate it later in:
- Frontend
- Sorting logic
- UI components

Overall Score must be stored as a separate value.

Formula:

Overall Score =
(Fit Score × 0.6) + (Success Score × 0.4)

Technical fit has slightly higher importance than hiring probability.

The stored Overall Score is the single source of truth for ranking.


==================================================
Data Model Changes
==================================================

Store these fields in the job analysis result:

- fit_score
- success_score
- overall_score

Do not derive overall_score dynamically from other fields after processing.


==================================================
Sorting and Ranking
==================================================

Update all job sorting and ranking logic.

Use:
- overall_score

Do not:
- recalculate scores during sorting
- combine Fit Score and Success Score again
- use old scoring aggregation logic


==================================================
Frontend Redesign
==================================================

Redesign the job cards and job drawer to display all three scores clearly.

Display:

1. Overall Score
- Primary ranking indicator
- Most prominent score

2. Technical Fit Score
- Shows how well the candidate matches the technical requirements

3. Success Score
- Shows the probability of getting hired


The UI should make the difference clear:

Example:

Overall Score: 87 (A+)
Technical Fit: 95 (A++)
Success Probability: 68 (B)


==================================================
Score Normalization and Grades
==================================================

If existing scores are not normalized to a 0-100 range:

- Convert them into a consistent 0-100 scale before displaying.
- Keep the original scoring logic unchanged.
- Normalization should only be for presentation.

The numeric score is the source of truth.
The grade is only a visual indicator.


Use this grading system:

90-100  → A++
80-89   → A+
70-79   → A
50-69   → B
30-49   → C
0-29    → D


Example:

Python Backend Engineer - Berlin

Overall Score:
87 (A+)

Technical Fit:
94 (A++)

Success Probability:
65 (B)


The user should immediately understand:
- High Fit Score = technically suitable
- High Success Score = realistic hiring chance
- High Overall Score = best ranking priority
