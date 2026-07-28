# Feature: Refactor Scoring Rules Into Entity-Based Rule Groups

## Goal

Refactor the current scoring rule system.

The current implementation incorrectly places all rules under Job Rules. Some rules belong to companies and should not affect job scoring.

Create a clean entity-based rule architecture.

The final rule structure should contain only these four groups:

1. Shared Rules
2. Job Rules
3. Product Company Rules
4. Recruiting Company Rules


---

# 1. Rule Scope Refactor

Update the rule model.

Each rule must have:

```text
id
name
description
category
score_type
priority
weight
rule_group
enabled

Replace the current scope logic with:

SHARED
JOB
COMPANY_PRODUCT
COMPANY_RECRUITING
2. Rule Application Logic
Job Processing

When processing a job:

Use only:

SHARED RULES
+
JOB RULES

Never apply:

COMPANY_PRODUCT RULES
COMPANY_RECRUITING RULES

Job scoring should generate:

job_fit_score

job_success_score

job_overall_score
Company Processing

First detect company type:

PRODUCT_COMPANY

RECRUITING_COMPANY

Then apply:

For Product Companies:

SHARED RULES
+
COMPANY_PRODUCT RULES

For Recruiting Companies:

SHARED RULES
+
COMPANY_RECRUITING RULES

Do not mix company rules with job rules.

3. Move Existing Rules

Move rules into correct groups.

Shared Rules

Move:

visa_and_relocation_compatibility

market_and_location_accessibility

communication_and_work_culture

sensitive_industry_penalty

Remove duplicated:

market_accessibility

Keep only:

market_and_location_accessibility
Job Rules

Keep only job-specific rules:

python_backend_core

role_alignment

hiring_probability

technical_synergy

engineering_depth

work_and_communication_fit
Product Company Rules

Move:

company_quality

engineering_culture

growth_and_career_potential

candidate_company_alignment
Recruiting Company Rules

Move:

recruiter_network_value

recruiter_market_access

recruiter_profile_alignment

recruiter_activity_and_opportunity
4. Database Migration

Create migration:

Existing rules should be reassigned to correct groups.
Do not create duplicate rules.
Preserve:
weight
priority
enabled status
descriptions

After migration:

Expected:

Shared Rules
4 rules


Job Rules
6 rules


Product Company Rules
4 rules


Recruiting Company Rules
4 rules
5. Rules Management UI Redesign

Replace current list layout with a Kanban board.

Display four columns:

------------------------------------------------
| Shared | Jobs | Product Company | Recruiting |
------------------------------------------------

Each column contains rule cards.

Each rule card shows:

Rule name
Category
Score type
Weight
Priority
Description
Enabled status
6. Kanban Features

Support:

Drag and drop rules between groups
Change priority by moving cards
Enable/disable rules
Edit rule details

When moving a rule:

Show confirmation:

"Changing rule group may affect scoring behavior."

7. Filters

Add filters:

All

Shared

Jobs

Product Company

Recruiting Company
8. Scoring Engine Validation

Add validation:

A Job processor must never load:

COMPANY_PRODUCT
COMPANY_RECRUITING

A Company processor must never load:

JOB

The scoring engine should dynamically load rules based on entity type.

9. Final Architecture Goal

The scoring engine should become extensible:

Adding future groups should not require changing core logic.

Example future groups:

COMPANY_INVESTOR

LEARNING_RESOURCE

NETWORK_CONTACT

The rule engine should only depend on:

entity_type
+
rule_group

not hardcoded conditions.
