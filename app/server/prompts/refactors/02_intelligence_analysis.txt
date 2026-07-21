Build a complete AI-powered Career Intelligence module, including backend architecture, database design, API layer, AI analysis workflow, and frontend dashboard.

The goal:
Create a career strategy system that helps a senior software engineer find relocation opportunities in Germany, Netherlands, and top European tech hubs.

This is not a simple analytics dashboard.
It should work as an AI career strategist:
- Analyze the job market
- Identify the highest-probability opportunities
- Recommend where to apply
- Identify skill gaps
- Recommend actions to increase hiring probability


==================================================
Product Navigation
==================================================

Use this application structure:

Career OS

1. Jobs
2. Intelligence
3. Profile
4. Rules
5. Settings


The new AI dashboard module should live under:

Intelligence


==================================================
Backend Requirements
==================================================


The system already has:

- Job records extracted from URLs
- Company information
- Location data
- Visa information
- Applicant information
- Required technologies
- Role information
- Seniority
- Fit Score
- Success Score
- Overall Score


Do not run AI analysis on every page load.


Create an AI analysis pipeline:


## Refresh All

Generate all intelligence sections.

## Section Refresh

Each intelligence section has its own refresh operation.

Examples:

POST:
/api/intelligence/refresh

POST:
/api/intelligence/market/refresh

POST:
/api/intelligence/opportunities/refresh

POST:
/api/intelligence/strategy/refresh

POST:
/api/intelligence/skills/refresh

POST:
/api/intelligence/company/refresh

POST:
/api/intelligence/networking/refresh


Store generated results in database.

Frontend should only consume cached analysis.


==================================================
Database Design
==================================================


Create:


DashboardAnalysis

Fields:

- id
- section_name
- generated_at
- snapshot_version
- metrics (JSON)
- charts_data (JSON)
- insights (JSON)
- recommendations (JSON)


Support:

- Full dashboard regeneration
- Individual section regeneration


Keep analysis history if possible to track market changes over time.


==================================================
AI Processing Architecture
==================================================


Do not send all jobs directly to the LLM.

Before AI processing:

Create aggregation layer:

Examples:

- Jobs by country
- Jobs by city
- Jobs by role
- Technology frequency
- Average scores
- Visa distribution
- Company ranking
- Skill demand
- Competition statistics


Send summarized market data to AI.

AI output must always follow:


Insight format:

Observation:
Evidence:
Impact:
Recommended Action:


Example:

Observation:
"Berlin has the highest number of Python backend opportunities."

Evidence:
"52% of matching jobs are located in Berlin."

Impact:
"Higher probability of finding visa-sponsored roles."

Action:
"Increase Berlin applications and networking."


==================================================
Intelligence Module Structure
==================================================


# 1. Market Intelligence


Purpose:
Understand the market.


Show:

Metrics:

- Total jobs
- High match jobs
- Apply now jobs
- Visa-ready jobs
- Remote jobs


Charts:

- Jobs by country
- Jobs by city
- Jobs by role
- Technology demand


AI Insights:

- Best countries
- Best cities
- Market trends
- Opportunities to prioritize


==================================================
# 2. Opportunity Radar


Purpose:
Find the best jobs.


Use:

- Fit Score
- Success Score
- Overall Score


Create:


Opportunity Matrix:

High Fit + High Success:
Apply immediately


High Fit + Medium Success:
Customize application


Medium Fit + High Success:
Consider applying


Low Fit:
Ignore


Show:


Top opportunities:

- Company
- Role
- Location
- Fit Score
- Success Score
- Overall Score
- Reason
- Recommended action


Important:

Ranking must use stored overall_score.

Never calculate ranking dynamically in frontend.


==================================================
# 3. Application Strategy


Purpose:
Tell the user what to do next.


Analyze:

- Fresh postings
- Competition
- Visa probability
- Overall score
- Company quality


Generate:


Action categories:

Apply Now:
Highest probability opportunities


Customize:
Strong fit but needs personalization


Network First:
Strong companies where direct contact improves chances


Avoid:
Low probability opportunities


Generate:

Daily actions:
Weekly goals:
Application priorities:


==================================================
# 4. Skill Intelligence


Purpose:
Find skills with highest career impact.


Do not rank only by frequency.


Calculate:

Skill ROI =
Market Demand
×
Current Gap
×
Career Alignment
×
Learning Impact


Classify:


Strong Skills:

Already competitive.


Maintain:

Keep improving.


High ROI:

Learn next.


Low Priority:

Ignore for now.


For every skill:

Show:

- Demand percentage
- Current level
- Gap
- Priority
- Expected impact


Example:

Kubernetes

Demand:
52%

Current:
Intermediate

Priority:
P1

Impact:
High


==================================================
# 5. Company Intelligence


Purpose:
Find target companies.


Analyze:


- Matching jobs
- Average scores
- Visa probability
- Hiring activity
- Technology alignment


Show:


Company ranking:

- Company name
- Location
- Matching roles
- Visa confidence
- Why target this company


==================================================
# 6. Networking Intelligence


Purpose:
Increase opportunities beyond applications.


Generate:


- Companies to follow
- Recruiters to contact
- Engineering managers
- Communities
- Open source opportunities


Recommend:

Who to contact:
Why:
Expected benefit:


==================================================
Frontend Requirements
==================================================


Create:

Intelligence page


Layout:


Header:

Career Intelligence

- Last updated timestamp
- Refresh All button


Each section/card:


- Section title
- Refresh button
- Loading state
- Last generated time


Display:


Metrics cards:

Example:

126
Jobs analyzed


71
High match


50
Apply now


Charts:

Use clear visualizations:
- Bar charts
- Distribution charts
- Matrix charts
- Trend charts


Insights cards:


Each insight card contains:

- Title
- Observation
- Evidence
- Impact
- Action


Recommendation cards:


Show:

Priority:
HIGH / MEDIUM / LOW

Action:
What to do

Reason:
Why it matters


==================================================
UI/UX Principles
==================================================


The dashboard should answer:

1. Where should I apply today?
2. Which companies maximize visa probability?
3. Which cities should I focus on?
4. Which skills increase my chances fastest?
5. What should I do this week?


Avoid:

- Generic statistics
- Vanity metrics
- Too many charts without actions
- Showing data without recommendations


The final product should feel like an AI career advisor combined with a job market intelligence platform.
