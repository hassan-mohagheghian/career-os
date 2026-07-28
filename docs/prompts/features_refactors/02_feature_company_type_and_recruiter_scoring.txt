feature_company_type_and_recruiter_scoring

Implement a company type classification system and update the company scoring architecture to handle recruiter companies differently from normal companies.

The goal is to avoid treating recruiting agencies/staffing companies like product/engineering companies. Recruiters can be highly valuable because they provide access to jobs, companies, and hiring networks, even though they do not have engineering culture or technical products.

The system should support different company evaluation strategies based on company type.

---

# 1. Add Company Type Classification

Add a new field to companies:

company_type

Supported values:

- PRODUCT_COMPANY
- RECRUITING_AGENCY
- STAFFING_COMPANY
- CONSULTING_COMPANY
- UNKNOWN


The company type should be detected during company processing using:

- Company name
- Website content
- User notes
- Extracted website information
- Business description


Examples:

Recruiting signals:

- "Recruitment"
- "Talent"
- "Hiring"
- "Staffing"
- "Executive search"
- "Tech recruiter"
- "Connecting engineers with companies"


Product company signals:

- SaaS
- Software product
- Platform
- Application
- Developer tools
- AI product


---

# 2. Refactor Company Scoring Engine

Currently:

Company scoring:

Shared Rules
+
Company Rules


Change to:

Company scoring:

Shared Rules
+
Company Type Specific Rules


Architecture:

Company
 |
 |-- Detect Company Type
 |
 |-- Apply Shared Rules
 |
 |-- Apply Product Company Rules
 |
 |-- Apply Recruiter Rules
 |
 |-- Apply Consulting Rules
 |
 |-- Generate Scores


---

# 3. Keep Shared Rules

Shared rules should continue applying to all companies:

- visa_and_relocation_compatibility
- market_and_location_accessibility
- communication_and_work_culture
- sensitive_industry_penalty


Do not duplicate these rules.

---

# 4. Update Product Company Rules

The current company rules should become Product Company Rules.

Rename:

Company Rules

to:

Product Company Rules


Apply only when:

company_type = PRODUCT_COMPANY


Keep:

## product_company_quality

Critical
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
- Good funding/revenue signals
- Market presence


---

## engineering_culture

Critical
Weight: 85

Evaluate:

Positive:

- Strong engineering team
- Technical blog
- Open source activity
- Modern technology stack
- Testing culture
- CI/CD
- Code review
- Architecture ownership
- Backend/platform engineering


---

## growth_and_career_potential

High
Weight: 75

Evaluate:

Positive:

- Senior ownership
- Technical leadership
- Mentorship
- Complex engineering challenges
- International growth


---

## candidate_company_alignment

Medium
Weight: 60

Evaluate:

Positive:

- Python backend
- Distributed systems
- Cloud-native systems
- AI infrastructure
- Developer tools
- Data platforms
- Rust/backend/platform teams


---

# 5. Add Recruiter Company Rules

Create a new section:

Recruiter Company Rules

Used only when:

company_type = RECRUITING_AGENCY
or
company_type = STAFFING_COMPANY


---

## recruiter_network_value

Type:
fit

Priority:
Critical

Weight:
100


Description:

Evaluate how valuable this recruiter is as a gateway to job opportunities.


Positive signals:

- Specialized in technology recruitment
- Backend/software engineering recruitment
- Works with Germany/Netherlands/EU companies
- Works with startups
- Has many active vacancies
- Represents multiple companies
- Has international candidate experience
- Has history hiring non-EU engineers


Negative signals:

- Generic recruitment
- Non-technical recruitment
- Low-quality staffing
- No evidence of technology hiring


Main impact:

Company Fit Score


---

## recruiter_market_access

Type:
success

Priority:
High

Weight:
85


Description:

Evaluate recruiter access to target markets.


Positive:

- Works with German companies
- Works with European startups
- Supports international candidates
- Works with English-speaking roles
- Understands relocation hiring


Negative:

- Local-only recruitment
- Only domestic candidates


Main impact:

Company Success Score


---

## recruiter_profile_alignment

Type:
fit

Priority:
High

Weight:
80


Description:

Evaluate if the recruiter can help the candidate find relevant positions.


Positive:

- Backend engineering roles
- Python roles
- AI engineering
- Cloud/platform roles
- Senior engineering positions
- Distributed systems roles


Negative:

- Frontend-only recruitment
- Junior mass recruitment
- Non-technical positions


Main impact:

Company Fit Score


---

## recruiter_activity_and_opportunity

Type:
success

Priority:
Medium

Weight:
70


Description:

Evaluate opportunity generation capability.


Positive:

- Many active jobs
- Frequently updated vacancies
- Multiple relevant companies
- Fast communication
- Dedicated recruiters


Negative:

- No recent activity
- Few relevant opportunities


Main impact:

Company Success Score


---

# 6. Company Scores

Keep the same three scores:

## company_fit_score

Meaning changes based on company type.

For Product Company:

"How well does this company match my career and technical profile?"


For Recruiter:

"How valuable is this company as a career opportunity gateway?"


---

## company_success_score

Measures probability of getting value from this company.

For Product Company:

- Visa
- Location
- Hiring accessibility
- Work environment


For Recruiter:

- Market access
- International hiring
- Active opportunities
- Response probability


---

## company_overall_score

Use the same formula:

overall =
fit_score * 0.5 +
success_score * 0.5


---

# 7. Frontend Changes

Company drawer should display company type.

Example:

Company Type:
Recruiting Agency


or:

Company Type:
Product Company


---

Add type-specific sections.

For Product Companies:

Show:

- Engineering culture
- Technology
- Product quality
- Career growth


For Recruiters:

Show:

- Recruitment specialization
- Target markets
- Supported roles
- Active opportunities
- Related jobs
- Contact/network information


---

# 8. Job Integration

When a job is connected to a company:

If company_type = RECRUITING_AGENCY:

Show a different company tab.

Example:

Company / Recruiter

Content:

- Recruiter specialization
- Related jobs
- Companies represented
- Opportunity value
- Recruiter score


Do not show irrelevant engineering culture sections.

---

# 9. Database Migration

Add:

companies.company_type

Create default:

UNKNOWN


Existing companies:

- Reprocess gradually
- Detect type automatically
- Keep backward compatibility


---

# 10. Requirements

- Do not remove existing company scoring.
- Keep shared rules reusable.
- Do not apply engineering rules to recruiters.
- Do not penalize recruiters because they are not technical companies.
- Make the rule engine extensible for future company types.
- Keep scoring transparent and explainable in the UI.
