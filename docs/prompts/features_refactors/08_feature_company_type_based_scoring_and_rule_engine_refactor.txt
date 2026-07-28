feature_company_type_based_scoring_and_rule_engine_refactor

## Goal

Refactor the scoring rule system to support different entity types and scoring strategies.

Currently, companies are scored mostly like product/engineering companies. This creates incorrect results for recruiting agencies because recruiters are not technical companies, but they can be highly valuable for finding jobs.

The new system should distinguish between:

1. Product Companies
2. Recruiting Agencies
3. Staffing Companies
4. Consulting Companies
5. Unknown Companies

Each type should have its own scoring rules while sharing common rules.

---

# 1. Update Rule Architecture

Refactor the rule model.

Every rule should support:


id
name
description
category
score_type
priority
weight
scope
enabled


Add:


scope


The scope defines where the rule is applied.

Supported scopes:


ALL
JOB
PRODUCT_COMPANY
RECRUITING_AGENCY
STAFFING_COMPANY
CONSULTING_COMPANY


---

# 2. Rule Execution Logic

## Job Processing

Apply:


ALL rules
+
JOB rules


Generate:


job_fit_score
job_success_score
job_overall_score


---

## Company Processing

First detect:


company_type


Then apply:


ALL rules
+
rules matching company_type


Example:


company_type = PRODUCT_COMPANY

Apply:

Shared Rules
+
Product Company Rules


Example:


company_type = RECRUITING_AGENCY

Apply:

Shared Rules
+
Recruiting Company Rules


Do not apply incompatible rules.

Example:

Do not apply:


engineering_culture


to:


RECRUITING_AGENCY


---

# 3. Add Company Type Detection

Add:


company_type


to company database model.

Values:


PRODUCT_COMPANY
RECRUITING_AGENCY
STAFFING_COMPANY
CONSULTING_COMPANY
UNKNOWN


Detect company type during company processing using:

- Company name
- Website content
- User notes
- Extracted website information
- Business description

Examples:


Recruiting signals:

- Recruitment
- Talent acquisition
- Hiring platform
- Staffing
- Executive search
- Tech recruiter
- Connecting candidates with companies


Product company signals:

- SaaS
- Software product
- Platform
- Developer tools
- AI product
- B2B product


---

# 4. Shared Rules

Create:


Shared Rules


These apply to:

- Jobs
- All company types


## visa_and_relocation_compatibility

Type:

success

Priority:

Critical

Weight:

100

Scope:

ALL


Evaluate:

Positive:

- Visa sponsorship
- Non-EU hiring history
- Relocation process
- International hiring


Negative:

- EU work authorization required
- No relocation support


---

## market_and_location_accessibility

Type:

success

Priority:

Critical

Weight:

90

Scope:

ALL


Merge and replace duplicate rules:

Remove:

- market_accessibility


Keep only:

market_and_location_accessibility


Evaluate:

Positive:

- Germany
- Berlin
- Munich
- Hamburg
- Netherlands
- Amsterdam
- Eindhoven
- Rotterdam
- Strong European tech hubs


Negative:

- Local-only markets
- Difficult immigration countries


---

## communication_and_work_culture

Type:

success

Priority:

High

Weight:

70

Scope:

ALL


Evaluate:

Positive:

- English-first workplace
- International teams
- Remote/hybrid
- Distributed teams
- Async communication


Negative:

- Mandatory local language
- Local-only environment


---

## sensitive_industry_penalty

Type:

success

Priority:

Medium

Weight:

50

Scope:

ALL


Keep existing logic.

Apply penalty for:

- Military/defense
- Surveillance
- Gambling
- Alcohol/tobacco
- Adult content
- Fraud-related businesses
- High-risk controversial industries


---

# 5. Job Rules

Keep:


Job Rules


Scope:

JOB


## python_backend_core

Weight:

100

Priority:

Critical


Evaluate:

Highest score for:

- Python
- Django
- FastAPI
- Flask
- SQLAlchemy
- Celery
- asyncio
- PostgreSQL
- Redis
- Kafka
- REST APIs
- Backend systems
- Distributed systems


Python must be the primary stack.


---

## role_alignment

Weight:

90

Priority:

Critical


Preferred:

Highest:

- Backend Engineer
- Senior Backend Engineer
- Python Backend Engineer
- Platform Engineer
- Distributed Systems Engineer


Good:

- Full Stack when Python backend is core
- AI Engineer with backend focus


Lower:

- Frontend only
- Mobile
- Data only


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
- High competition
- Generic hiring


---

## technical_synergy

Weight:

70


Bonus:

Frontend:

- TypeScript
- React
- Next.js
- Tailwind
- shadcn/ui
- TanStack


Rust:

- Rust
- Axum
- Tokio
- Serde
- Systems programming


Rules:

- Frontend is valuable only when backend is primary.
- Rust is valuable when Python/backend experience transfers.
- Do not prioritize pure senior Rust roles.


---

## engineering_depth

Weight:

60


Bonus:

- Distributed systems
- Microservices
- Kubernetes
- Docker
- Linux
- AWS/GCP/Azure
- CI/CD
- Kafka
- Event-driven systems


---

# 6. Product Company Rules

Create:


Product Company Rules


Scope:

PRODUCT_COMPANY


## company_quality

Weight:

100

Priority:

Critical


Evaluate:

Positive:

- SaaS
- AI infrastructure
- Developer tools
- FinTech
- HealthTech
- B2B platforms
- Strong funding
- Revenue signals
- Product maturity


---

## engineering_culture

Weight:

85


Evaluate:

Positive:

- Strong engineering team
- Technical blog
- Open source
- Testing culture
- CI/CD
- Code review
- Architecture ownership
- Backend/platform teams


---

## growth_and_career_potential

Weight:

75


Evaluate:

Positive:

- Senior ownership
- Leadership path
- Mentorship
- Complex engineering challenges


---

## candidate_company_alignment

Weight:

60


Evaluate:

Positive:

- Python backend
- Distributed systems
- Cloud-native
- AI infrastructure
- Data platforms
- Developer tools
- Rust/backend/platform teams


---

# 7. Recruiting Company Rules

Create:


Recruiting Company Rules


Scope:

RECRUITING_AGENCY

STAFFING_COMPANY


Recruiters should not be scored based on engineering culture.

Their value is opportunity access.


---

## recruiter_network_value

Type:

fit

Weight:

100

Priority:

Critical


Evaluate:

Positive:

- Technology recruitment
- Backend/software engineering focus
- Works with startups
- Works with Germany/EU companies
- Represents many companies
- International candidate experience
- Non-EU hiring experience


Negative:

- Generic recruitment
- Non-technical recruitment
- Low-quality staffing


---

## recruiter_market_access

Type:

success

Weight:

85


Evaluate:

Positive:

- German market access
- European startup network
- English-speaking jobs
- Relocation candidates


Negative:

- Local-only recruitment


---

## recruiter_profile_alignment

Type:

fit

Weight:

80


Evaluate:

Positive:

- Backend roles
- Python roles
- AI engineering
- Cloud/platform roles
- Senior engineering recruitment


Negative:

- Frontend-only
- Junior mass recruitment


---

## recruiter_activity_and_opportunity

Type:

success

Weight:

70


Evaluate:

Positive:

- Many active jobs
- Recent vacancies
- Multiple clients
- Fast communication


Negative:

- No recent activity


---

# 8. Company Score Calculation

Every company should have:


company_fit_score

company_success_score

company_overall_score



## Product Company Meaning

Fit:

Technical and career match.


Success:

Probability of successful hiring and relocation.


---

## Recruiter Meaning

Fit:

How valuable this recruiter is for finding suitable jobs.


Success:

Probability that this recruiter creates opportunities.


---

Overall:


overall_score =
(fit_score * 0.5) +
(success_score * 0.5)


Do not calculate it by simply adding other scores.

---

# 9. Frontend Rules Management UI

Update Rules page.

Current:


Shared Rules
Job Rules
Company Rules


Change to:


Shared Rules

Job Rules

Company Rules

Product Company Rules

Recruiting Company Rules

Staffing Company Rules

Consulting Company Rules



Each rule card must display:

- Rule name
- Scope
- Category
- Score type
- Weight
- Priority
- Description


Add filters:


All

Shared

Jobs

Product Companies

Recruiters

Staffing

Consulting



Allow:

- Enable/disable rule
- Edit weight
- Edit priority
- Edit description

---

# 10. Company UI Changes

Company drawer should display:


Company Type


Example:


Company Type:
Recruiting Agency



For Product Company show:

Tabs:

- Overview
- Engineering Culture
- Technology
- Career
- Scores


For Recruiter show:

Tabs:

- Overview
- Recruitment Focus
- Markets
- Related Jobs
- Network Value
- Scores


---

# 11. Job Drawer Integration

When a job has a linked company:


If:


PRODUCT_COMPANY


Show normal company intelligence.


If:


RECRUITING_AGENCY


Show recruiter intelligence:

- Recruiter specialization
- Supported markets
- Related jobs
- Represented companies
- Recruiter scores
- Contact/network information


---

# 12. Migration

Requirements:

- Keep existing data.
- Existing companies default to UNKNOWN.
- Existing rules should be migrated to new scopes.
- Remove duplicate market rule.
- Do not break existing job scoring.
- Make the rule engine extensible for future company types.

The final architecture should support adding new entity types and scoring strategies without changing the core scoring engine.
