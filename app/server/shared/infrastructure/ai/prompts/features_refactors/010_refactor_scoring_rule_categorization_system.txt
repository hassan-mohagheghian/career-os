# Refactor Scoring Rule Categorization System

## Goal

Refactor the current scoring rule system by correctly assigning each rule to the proper entity scope.

The current problem:
Many rules are incorrectly placed under Job Rules even though they belong to companies or shared evaluation.

The system should support different scoring contexts:

1. Shared Rules
2. Job Rules
3. Product Company Rules
4. Recruiting Company Rules
5. Staffing / Consulting Rules (optional)

---

# Step 1 — Analyze Existing Rules

Review all existing scoring rules.

For each rule:

- Determine its real ownership.
- Decide whether it evaluates:
  - Job opportunity
  - Company
  - Recruiter / Staffing company
  - Candidate alignment
  - Global relocation suitability

Do not simply move rules.
Improve names, descriptions, weights, and scoring impact where needed.

---

# Step 2 — Create Rule Categories

Create these rule groups:

## 1. Shared Rules

Rules applied to all entities:

Move or create:

### visa_and_relocation_compatibility

Purpose:
Evaluate whether this opportunity/company helps relocation.

Weight:
100

---

### market_and_location_accessibility

Purpose:
Evaluate target market accessibility.

Priority:
Germany:
- Berlin
- Munich
- Hamburg

Netherlands:
- Amsterdam
- Eindhoven
- Rotterdam

Positive:
- Spain
- Sweden
- Denmark
- Switzerland
- Austria

---

### communication_and_work_culture

Purpose:
Evaluate international communication compatibility.

Positive:
- English-first
- International teams
- Remote/hybrid
- Distributed teams

Negative:
- Local language mandatory
- Local-only environment

---

### sensitive_industry_penalty

Purpose:
Reduce score for industries that are not preferred.

Include:

- Military
- Defense
- Weapons
- Surveillance
- Gambling
- Betting
- Alcohol
- Tobacco
- Adult content
- Fraud-related businesses

Do not heavily penalize normal SaaS/security companies.

---

# 2. Job Rules

Only rules related to a specific job position.

Move/create:

## python_backend_core

Weight:
100

Evaluate:
- Python
- Django
- FastAPI
- Flask
- SQLAlchemy
- PostgreSQL
- Redis
- Kafka
- REST
- Backend systems

---

## role_alignment

Weight:
90

Evaluate:

Highest:
- Backend Engineer
- Senior Backend Engineer
- Python Backend Engineer
- Platform Engineer
- Distributed Systems Engineer

Good:
- Full Stack with backend ownership
- AI Engineer with backend focus

Lower:
- Frontend only
- Mobile only
- Data only

---

## technical_synergy

Weight:
70

Evaluate:

Bonus:
- TypeScript
- React
- Next.js
- Rust
- Tokio
- Axum

Only add bonus when backend remains primary.

---

## engineering_depth

Weight:
60

Evaluate:

- Distributed systems
- Microservices
- Kubernetes
- Docker
- Cloud
- Kafka
- Event-driven architecture
- Senior ownership

---

## hiring_probability

Weight:
80

Evaluate:

Positive:
- Fresh posting
- Low applicants
- Specialized role
- Clear requirements

Negative:
- Old posting
- Mass hiring
- High competition

---

## candidate_job_alignment

Create this new rule.

Evaluate how well the specific job matches the candidate profile.

Consider:
- Seniority
- Backend focus
- Python
- Distributed systems
- Cloud-native engineering
- AI/backend overlap


---

# 3. Product Company Rules

Create new category.

Move:

## company_quality

Weight:
100

Evaluate:

Positive:
- SaaS
- AI infrastructure
- Developer tools
- FinTech
- HealthTech
- B2B platforms
- Good funding
- Strong market position


---

## engineering_culture

Weight:
85

Evaluate:

- Engineering blog
- Open source
- Testing culture
- CI/CD
- Architecture ownership
- Senior engineers


---

## growth_and_career_potential

Weight:
75

Evaluate:

- Senior ownership
- Leadership path
- Mentorship
- Technical challenges


---

## candidate_company_alignment

Weight:
60

Evaluate:

Match with:

- Python backend
- Distributed systems
- Cloud-native
- AI infrastructure
- Developer platforms


---

## product_maturity

Create new rule.

Evaluate:

- Real product
- Customers
- Revenue signals
- Market adoption
- Stability


---

# 4. Recruiting Company Rules

Create new category.

Move:

## recruiter_network_value

Weight:
100

Evaluate:

- Technology recruitment
- Backend/software focus
- EU companies
- International candidates
- Visa experience


---

## recruiter_market_access

Weight:
85

Evaluate:

- Germany access
- Netherlands access
- Startup network
- English roles


---

## recruiter_profile_alignment

Weight:
80

Evaluate:

Recruiter specialization:

Positive:
- Backend
- Python
- AI
- Cloud
- Senior engineering

Negative:
- Generic recruitment
- Non-technical


---

## recruiter_activity_and_opportunity

Weight:
70

Evaluate:

- Number of active roles
- Company network
- Recent activity


---

## recruiter_quality

Create new rule.

Evaluate:

- Reputation
- Transparency
- Communication quality
- Candidate experience


---

# Step 3 — Backend Changes

Update database models:

Add:


rule_category:

shared
job
product_company
recruiting_company
staffing_company

Each rule should contain:


name
description
category
impact_type
weight
priority
active


---

# Step 4 — Processing Logic

Update scoring pipeline.

Job processing:

Use:

Shared Rules
+
Job Rules
+
Assigned Company Rules


Company processing:

Product company:

Shared Rules
+
Product Company Rules


Recruiting company:

Shared Rules
+
Recruiting Company Rules


Staffing:

Shared Rules
+
Staffing Rules


---

# Step 5 — Frontend UI

Replace current tabs with Kanban-style rule management.

Columns:

1. Shared
2. Jobs
3. Product Companies
4. Recruiting Companies
5. Staffing / Consulting


Each column shows:

- Rule count
- Active rules
- Add Rule button
- Edit/Delete actions

Rules can be dragged only if supported, otherwise keep category selection.

---

# Step 6 — Migration

Do not delete existing rules.

Create migration:

- Move rules to correct categories.
- Rename duplicated rules.
- Remove duplicated logic.
- Keep scoring behavior consistent where possible.

After migration verify:

- Job scoring still works.
- Company scoring uses company rules.
- Recruiter companies have separate scoring behavior.
- Shared rules affect all entities correctly.
