id="company_intelligence_complete_feature"

Implement a complete AI-powered Company Intelligence feature inside the Jobs module.

The goal of this feature is to build a structured company knowledge base connected to the job search workflow.

This feature should help a senior software engineer evaluate companies as potential future employers, especially for relocation opportunities in Germany, Netherlands, and other European tech hubs.

This is not a simple company directory.
It should behave as an AI company research assistant that answers:

- Is this company a good target employer?
- Is relocation realistic?
- Does this company match my technical background?
- What is the engineering culture?
- What should I know before applying or contacting recruiters?


==================================================
Navigation Structure
==================================================

Update the application navigation:


Jobs

├── All Jobs
├── Applications
└── Companies


Companies should be a sub-module of Jobs because companies are directly connected to job opportunities and applications.


==================================================
Feature Overview
==================================================

Users can add companies manually or through URLs.

Supported inputs:

1. Company website URL

Example:
https://company.com


2. Manual company notes

Example:

"Berlin AI startup building developer tools"


The system should create an AI processing workflow similar to the existing Job processing workflow.


==================================================
Company Processing Workflow
==================================================

Create a background processing pipeline.


Statuses:


Pending

New company waiting for processing.


Queued

Company added to processing queue.


Processing

AI extraction is running.


Failed

Processing failed with error details.


Completed

Company intelligence generated successfully.


The workflow should support:

- Retry failed processing
- Reprocess company
- Refresh company intelligence


==================================================
Company Page UI
==================================================

Create a Companies page under Jobs.


Use the same design language as the Jobs page.


Layout:

Two-column interface.


==================================================
LEFT COLUMN
==================================================

Processing Queue


Show sections:


Pending

Queued

Processing

Failed


Each section should have:

- Header
- Count badge
- Company cards


Each processing item displays:

- Company name (if detected)
- URL
- Added date
- Processing status
- Error message if failed


Actions:

- Retry
- Cancel
- Process now


==================================================
RIGHT COLUMN
==================================================

Processed Companies


Display company cards.


Each card should show:


Basic information:

- Company name
- Logo if available
- Industry
- Country
- City
- Website
- Company size
- Company type


Important indicators:


Visa Score:
0-100


Technology Match:
0-100


Career Opportunity:
0-100


Company Priority:

A++
A+
A
B
C


Example:


Cara Care

Berlin, Germany

Healthcare SaaS

Visa:
90

Technology Match:
92

Career:
85

Priority:
A+


==================================================
Company Drawer
==================================================

Clicking a company opens a detailed drawer.


The drawer should contain:


# Overview


Extract:

- Company name
- Description
- Products/services
- Industry
- Founded year
- Headquarters
- Countries of operation
- Company size


==================================================
Employer Intelligence
==================================================


Analyze the company as an employer.


## Engineering Culture


Extract:


- Engineering organization
- Team structure
- Development methodology
- Technical decision process
- Engineering maturity
- Startup vs enterprise environment
- Quality culture
- Open source activity


Example:

"Strong engineering culture with autonomous teams and modern backend practices."


## International Environment


Analyze:


- English usage
- International employees
- Global teams
- Remote collaboration
- Diversity indicators


Generate:


International Score:

0-100


==================================================
Career Opportunity Analysis
==================================================


Analyze:


- Senior engineer opportunities
- Technical challenges
- Growth potential
- Learning opportunities
- Career progression
- Engineering impact


Generate:


Career Score:

0-100


==================================================
Benefits & Work Environment
==================================================


Extract:


- Salary information if available
- Benefits
- Remote policy
- Hybrid policy
- Vacation
- Learning budget
- Equipment support
- Relocation support


==================================================
Relocation Intelligence
==================================================


This section is very important.


Analyze:


Visa signals:

- Previous sponsorship history
- International hiring
- Relocation programs
- English-first environment
- Country restrictions


Generate:


Visa Score:

0-100


Relocation Recommendation:


HIGH

MEDIUM

LOW


Include:


Positive signals:

Risks:

Recommended approach:


Example:


Positive:
"Company has history hiring international engineers."


Risk:
"Most roles require German language."


Recommendation:
"Apply only to English-speaking engineering roles."


==================================================
Technology Intelligence
==================================================


Extract:


Technology stack:


Backend:
- Python
- Django
- FastAPI
- Java
- Go
- Rust


Frontend:
- React
- TypeScript


Infrastructure:

- Kubernetes
- AWS
- Docker
- Terraform


Data:

- PostgreSQL
- Kafka
- Redis


Compare with candidate profile.


Generate:


Technology Match Score:

0-100


Explain:


Why this company matches:

Missing technologies:

Potential learning opportunities:


==================================================
AI Company Recommendation
==================================================


Generate:


Company Priority:


A++

A+

A

B

C


Based on:


- Technical match
- Visa probability
- Company quality
- Growth opportunity
- International environment


Every recommendation must include:


Observation:

Evidence:

Impact:

Recommended Action:


Example:


Observation:
"Company strongly matches backend profile."

Evidence:
"Uses Python, FastAPI, PostgreSQL and Kubernetes."

Impact:
"High chance of technical interview success."

Action:
"Prioritize direct application and recruiter outreach."


==================================================
Database Design
==================================================


Create:


Company


Fields:


id

name

website

domain

industry

country

city

description

company_size

company_type

logo_url

processing_status

created_at

updated_at


----------------------------------


CompanyIntelligence


Fields:


id

company_id

overview

culture_analysis

international_analysis

career_analysis

benefits_analysis

visa_analysis

technology_analysis

recommendation

scores

raw_source_data

generated_at


----------------------------------


CompanySource


Fields:


id

company_id

url

source_type

content

created_at


==================================================
AI Processing Architecture
==================================================


Do not call AI every time the drawer opens.


Use cached intelligence.


Pipeline:


1. Fetch company sources

2. Extract relevant information

3. Summarize information

4. Generate structured intelligence

5. Calculate scores

6. Store results


AI output should be structured JSON.


==================================================
Job Integration
==================================================


Extend existing Job functionality.


Currently jobs contain company information extracted during job processing.


Add:


Job → Company relationship


Support:


1. Automatically suggest matching companies.

2. Manually assign a company.

3. Create company from job.


Matching signals:


- Company name
- Domain
- Website
- Company identifiers


==================================================
Job Drawer Update
==================================================


Add a new tab:


Company


inside the Job drawer.


If the job is linked to a company:


Display:


Company Overview:

- Name
- Industry
- Location
- Description


Company Intelligence:

- Engineering culture
- International environment
- Visa score
- Technology match
- Career opportunity


Recommendation:


Why this company is worth applying to.


==================================================
Frontend Requirements
==================================================


Follow existing Jobs UI patterns.


Create:


Companies page


Features:


- Add Company button
- URL input
- Description input
- Processing queue
- Company cards
- Company drawer


Include:


- Status badges
- Score badges
- Loading states
- Empty states
- Error states
- Retry actions
- Reprocess action


==================================================
Future Compatibility
==================================================


Design this feature so it can later support:


- Company tracking
- Application history
- Interview preparation
- Recruiter management
- Company notes
- Networking activities


==================================================
Final Goal
==================================================


The final feature should create a Company Intelligence layer connected to job search.

The user should be able to quickly understand:


1. Which companies are worth targeting?

2. Which companies are realistic for relocation?

3. Which companies match my technical skills?

4. What is the company culture?

5. What should I know before applying?

6. How should I approach this company?


The result should feel like an AI-powered company research assistant integrated into a professional job search platform.
