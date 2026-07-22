refactor_rule_system

Refactor the existing scoring rule system to support three rule categories instead of only job-specific rules.

Goal:
Create a scalable rule architecture where:
1. Shared Rules are reusable across Job and Company processing.
2. Job Rules are only used for job scoring.
3. Company Rules are only used for company scoring.

The system should calculate scores using the correct rule groups during processing.

## Backend Changes

### 1. Extend Rule Model

Update the rule system/database schema to support rule categories:

Rule categories:

- shared
- job
- company

Each rule should have:
- name
- category
- priority
- score_weight
- description
- active status
- configuration if needed

Keep backward compatibility with existing job rules.

---

## 2. Add Default Shared Rules

Create default shared rules in the database:

### visa_and_relocation_compatibility
Priority: Critical
Weight: 100

Evaluate:
Positive:
- Work visa sponsorship
- EU Blue Card support
- History of hiring non-EU engineers
- Relocation support
- International hiring process

Negative:
- EU work authorization required
- Local candidates only
- No relocation support

Main impact:
Success Score


---

### market_and_location_accessibility
Priority: Critical
Weight: 90

Evaluate:

Highest priority:
- Germany:
  - Berlin
  - Munich
  - Hamburg

- Netherlands:
  - Amsterdam
  - Eindhoven
  - Rotterdam

Other positive European tech hubs:
- Spain
- Sweden
- Denmark
- Switzerland
- Austria

Negative:
- Local-only markets
- Difficult immigration countries

Main impact:
Success Score


---

### communication_and_work_culture
Priority: High
Weight: 70

Evaluate:

Positive:
- English-first workplace
- International teams
- Remote/hybrid options
- Distributed teams
- Async communication culture

Negative:
- German/French/etc mandatory
- Local-only communication

Main impact:
Success Score


---

### sensitive_industry_penalty
Priority: Medium
Weight: 50

Reduce score for sensitive industries:

- Defense and military
- Weapons systems
- Intelligence agencies
- Surveillance platforms
- Gambling and betting
- Alcohol and tobacco
- Adult content
- Fraud-related industries
- Highly controversial industries

Apply stronger penalties when the core business is related to these areas.

Do not heavily penalize normal technology companies that only serve these industries.

Main impact:
Success Score


---

# 3. Add Default Company Rules

Create these default company rules:

## company_quality
Priority: Critical
Weight: 100

Evaluate:

Positive:
- Strong product company
- SaaS
- Developer tools
- AI infrastructure
- FinTech
- HealthTech
- B2B platforms
- Good funding or revenue signals
- Product maturity
- Market presence

Negative:
- Weak product signals
- Unclear business model
- Very unstable companies


---

## engineering_culture
Priority: High
Weight: 85

Evaluate:

Positive:
- Strong engineering team
- Technical blog
- Open source activity
- Modern technology stack
- Testing culture
- CI/CD practices
- Code review
- Architecture ownership
- Senior engineering environment
- Backend/platform engineering teams


---

## growth_and_career_potential
Priority: High
Weight: 75

Evaluate:

Positive:
- Senior ownership opportunities
- Technical leadership path
- Mentorship
- Learning culture
- Complex technical challenges
- International growth opportunities

Negative:
- Maintenance-only products
- Limited engineering growth


---

## candidate_company_alignment
Priority: Medium
Weight: 60

Evaluate alignment with candidate profile:

Positive:
- Python backend
- Distributed systems
- Cloud-native systems
- AI infrastructure
- Developer tools
- Data platforms

Additional bonus:
- Rust usage
- Backend/platform teams

Negative:
- Pure frontend companies
- Mobile-only companies
- Hardware-only companies


---

# 4. Processing Changes

## Job Processing

When processing a job:

Use:
- Shared Rules
- Job Rules

Do NOT use:
- Company Rules


Job scoring should calculate:

- job_fit_score
- job_success_score
- job_overall_score


---

## Company Processing

When processing a company:

Use:
- Shared Rules
- Company Rules

Do NOT use:
- Job Rules


Company scoring should calculate:

- company_fit_score
- company_success_score
- company_overall_score


---

# Frontend Changes

Update the Rules management UI.

Currently:
- Job Rules only

Change to:

Rules
 ├── Shared Rules
 ├── Job Rules
 └── Company Rules


Each section should have:
- Rule list
- Priority
- Weight
- Active status
- Edit functionality
- Add rule functionality


Keep the current UI style and behavior.

---

# Migration Requirements

- Existing Job Rules must remain unchanged.
- Existing scores should not break.
- Existing jobs should continue using the new rule engine automatically.
- Existing company processing should start using Company + Shared rules.

Create clean separation between:
- Rule definition
- Rule evaluation
- Score calculation

The architecture should allow adding new rule categories in the future without another major refactor.
