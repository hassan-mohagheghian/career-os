# Implement Job Application Workspace

We already have an existing Job Search / Career Intelligence application.

The system already analyzes jobs, companies, and the user's profile. It also extracts and stores structured intelligence from these analyses.

Your task is to implement a **Job Application Workspace** for a selected/recommended job.

The most important requirement is:

> **Do not re-analyze information that the system already knows. Reuse the existing structured analysis and derived data as input/context for all application preparation features.**

The new Application Workspace must build on top of the existing intelligence rather than creating a second, independent analysis pipeline.

---

# 1. Existing Intelligence to Reuse

Before implementing anything, inspect the existing domain models, services, APIs, database schema, and AI outputs.

The Application Workspace should reuse as much existing structured information as possible.

## Job Intelligence

Reuse existing Job analysis such as:

- Job description
- Responsibilities
- Requirements
- Required skills
- Preferred skills
- Hard skills
- Soft skills
- Seniority
- Experience requirements
- Domain requirements
- Language requirements
- Location
- Work type
- Employment type
- Keywords
- Job score
- Fit score
- Success score
- Overall score
- Existing Job/User skill matching
- Existing skill gaps
- Existing recommendation/reasoning

Do not ask the LLM to rediscover these facts from the raw job description if they are already available as structured data.

---

## Company Intelligence

Reuse existing Company analysis such as:

- Company description
- Products/services
- Industry/domain
- Company type
- Technology information
- Engineering context
- Company characteristics
- Relevant company keywords
- Existing company analysis
- Any available company-specific insights

Use this information to make the application materials and recommendations company-specific.

Do not perform a completely new company analysis unless existing data is insufficient.

---

## User Intelligence

Reuse all existing user-related analysis, including:

### Resume

- Uploaded resume
- Parsed resume data
- Work experience
- Projects
- Education
- Certifications
- Existing skills
- Technologies
- Achievements
- Existing resume analysis

### LinkedIn

- LinkedIn profile data
- Headline
- About
- Experience
- Skills
- Projects
- Education
- Other extracted information

### User Skills

- Extracted skills
- Skill categories
- Skill aliases
- Skill proficiency
- Skill confidence
- Evidence for each skill
- Skill frequency where available

### Existing User/Job Analysis

Reuse:

- Skill match
- Skill gap
- Transferable skills
- Strong matches
- Weak matches
- Missing skills
- Critical gaps
- Existing recommendation reasoning

---

# 2. Core Principle

The processing pipeline should conceptually be:

```text
Existing Job Intelligence
          +
Existing Company Intelligence
          +
Existing User Intelligence
          +
Existing Job/User Gap Analysis
          ↓
   Application Intelligence
          ↓
Preparation + Resume + Cover Letter
```

NOT:

```text
Raw Job
  ↓
Analyze Job Again
  ↓
Analyze Company Again
  ↓
Analyze User Again
  ↓
Generate Application
```

Reuse existing intelligence wherever possible.

Only perform additional LLM processing when it produces a genuinely new application-specific result.

---

# 3. UX Architecture

Do NOT create a nested drawer.

The architecture is:

```text
Jobs List
   │
   ├── Application button
   │
   └── Job Detail Drawer
          │
          ├── Edit
          └── Application
```

Both Application buttons navigate to:

```text
/jobs/{job_id}/application
```

The Application Workspace is a dedicated full page.

---

# 4. Application Page Header

The page must clearly identify the target job.

Show:

- Back to Job
- Job title
- Company
- Location
- Employment/work type
- Job score / recommendation
- Application status

Example:

```text
← Back to Job

Senior Backend Engineer
Company X · Berlin, Germany

A+ · 91% Match

Status: Preparing
```

---

# 5. Application Status & Dates

Keep the MVP simple.

Statuses:

```text
Recommended
Preparing
Ready to Apply
Applied
Rejected
Withdrawn
```

Allow the user to enter:

### Applied Date

```text
Applied: [ date ]
```

### Follow-ups

Allow multiple follow-ups.

Each follow-up contains:

```text
Follow-up Date
Note
Completed
```

Example:

```text
Follow-ups

Aug 20
Follow up with recruiter
[ ] Completed

Aug 27
Second follow-up
[ ] Completed

[ + Add Follow-up ]
```

Do not build a complex CRM.

---

# 6. Preparation

Create a **Preparation** section.

The preparation plan must be generated from existing:

```text
Job Requirements
+
Job Skills
+
User Skills
+
User Proficiency
+
User Evidence
+
Existing Job/User Gap Analysis
+
Company Intelligence
```

Do not simply list missing skills.

The goal is to tell the user exactly:

- What they should improve
- Why it matters for this job
- What specifically to learn
- How to practice it
- What resources to use
- How much effort is likely required
- What priority it has

---

# 7. Hard Skills

For each meaningful hard-skill gap, generate:

```text
Skill
Gap Level
Priority
Why it matters
What to learn
How to practice
Recommended resources
Estimated effort
```

Example:

```text
Kubernetes

Gap: Medium
Priority: High
Estimated effort: 6 hours

Why:
This job explicitly requires Kubernetes and the
user has limited demonstrated experience.

What to learn:
- Deployments
- Services
- ConfigMaps
- Health checks

How to practice:
- Read Kubernetes documentation
- Deploy a FastAPI application locally
- Create a Deployment and Service
- Practice rolling updates

Resources:
- Kubernetes documentation
- Relevant hands-on tutorials
```

Recommendations must be concrete.

Avoid generic recommendations such as:

```text
Learn Kubernetes.
```

Instead use:

```text
What → Why → How → Resources
```

---

# 8. Soft Skills

Generate a similar preparation plan for relevant soft skills.

Example:

```text
System Design Communication

Gap: Medium
Priority: High

Why:
The role requires communicating architecture
and technical trade-offs.

What to improve:
- Explaining architecture clearly
- Discussing trade-offs
- Communicating technical decisions

How to practice:
- Explain one architecture in 5 minutes
- Practice trade-off questions
- Prepare real examples from previous projects
```

Only recommend soft skills that are relevant to the job or identified as meaningful gaps.

---

# 9. Preparation Prioritization

Do not recommend learning every missing skill.

Prioritize according to:

1. Explicit job requirements
2. Important skill gaps
3. Critical blockers
4. Skills where the user has partial/transferable experience
5. Skills with high impact on application readiness
6. Skills that can realistically be improved in a reasonable amount of time

Use:

```text
High
Medium
Low
```

The objective is:

> Find the smallest set of improvements that can materially increase the quality of the application.

---

# 10. Tailored Resume

Create an **Application Documents** section.

Generate a job-specific resume using existing intelligence.

Input/context should include:

```text
Existing Resume
+
Parsed Resume Data
+
LinkedIn Analysis
+
User Skills
+
User Skill Evidence
+
Job Analysis
+
Job Requirements
+
Job Skills
+
Job/User Skill Gap Analysis
+
Company Analysis
```

The LLM should not need to independently rediscover these facts.

---

# 11. Resume Tailoring Rules

The tailored resume should:

- Highlight relevant experience
- Highlight relevant projects
- Prioritize relevant skills
- Use relevant terminology from the job
- Improve ATS relevance
- Reflect the company's context when appropriate
- Preserve factual accuracy
- Use evidence already present in the user's profile

Never invent:

- Experience
- Employers
- Projects
- Technologies
- Achievements
- Responsibilities
- Certifications
- Education
- Job titles

If a requirement is missing, do not fabricate it.

Use existing evidence to distinguish:

```text
Strong evidence
Partial / transferable evidence
Missing evidence
```

---

# 12. Resume UX

Initial state:

```text
Resume

Base Resume
Available

Tailored Resume
Not generated

[ Generate Tailored Resume ]
```

After generation:

```text
Tailored Resume
Version 1

[ View ]
[ Edit ]
[ Regenerate ]
[ Download ]
```

Store generated resumes as versioned application documents.

---

# 13. Cover Letter

Generate a job-specific and company-specific Cover Letter using:

```text
Job Intelligence
+
Company Intelligence
+
User Resume
+
LinkedIn Intelligence
+
User Skills
+
Relevant User Experience
+
Tailored Resume
```

The Cover Letter should:

- Explain why this role is relevant
- Explain why the company is relevant
- Highlight the strongest matching experience
- Use real user evidence
- Be concise and professional
- Avoid generic content
- Never invent information

UX:

```text
Cover Letter

Not generated

[ Generate Cover Letter ]
```

After generation:

```text
Cover Letter
Version 1

[ View ]
[ Edit ]
[ Regenerate ]
[ Copy ]
```

Store it as a versioned application document.

---

# 14. Application Workspace Structure

Use:

```text
Application Page
│
├── Job Context / Header
│
├── Application
│   ├── Status
│   ├── Applied Date
│   └── Follow-ups
│
├── Preparation
│   ├── Hard Skills
│   └── Soft Skills
│
└── Application Documents
    ├── Tailored Resume
    └── Cover Letter
```

Keep the page focused.

Do not add Interview functionality yet.

---

# 15. Data Model

Introduce only the minimum required concepts.

Conceptually:

```text
Application
├── id
├── job_id
├── status
├── applied_at
├── created_at
└── updated_at

ApplicationFollowUp
├── id
├── application_id
├── scheduled_at
├── note
├── completed_at
└── created_at

ApplicationDocument
├── id
├── application_id
├── type
├── version
├── content / file reference
├── status
└── created_at
```

Document types:

```text
TAILORED_RESUME
COVER_LETTER
```

Do not over-engineer this.

---

# 16. AI Processing Architecture

Application-specific AI processing should consume existing structured intelligence.

Conceptually:

```text
                 ┌─────────────────────┐
                 │   Job Intelligence  │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Company Intelligence│
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │  User Intelligence  │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Existing Gap Analysis│
                 └──────────┬──────────┘
                            │
                            ▼
                 Application Intelligence
                       ┌────┼────┐
                       │    │    │
                       ▼    ▼    ▼
                   Prepare Resume Cover Letter
```

Avoid duplicating existing analysis pipelines.

---

# 17. Data Grounding

All generated content must be grounded in stored application/user/job/company data.

The LLM may:

- Reorganize
- Rewrite
- Summarize
- Tailor
- Generate recommendations
- Generate preparation plans

The LLM must NOT invent user facts.

When there is insufficient evidence, explicitly indicate:

```text
Missing evidence
```

or:

```text
Not demonstrated
```

---

# 18. Implementation Requirements

Before writing code:

1. Inspect the existing repository.
2. Inspect the current Job Detail Drawer.
3. Inspect existing Jobs List components.
4. Inspect routing.
5. Inspect Job models and APIs.
6. Inspect Company models and analysis outputs.
7. Inspect User/Profile models.
8. Inspect Resume and LinkedIn analysis outputs.
9. Inspect Skill models.
10. Inspect existing Job/User matching and gap-analysis logic.
11. Inspect existing AI/LLM infrastructure.
12. Identify reusable services, schemas, components, and prompts.

Then propose the smallest implementation required.

Do NOT rebuild existing functionality.

Do NOT introduce duplicate Job/Company/User analysis.

Do NOT introduce a new UI framework.

Reuse the existing design system and architecture.

---

# 19. Acceptance Criteria

### Navigation

- [ ] Application button exists in Jobs List
- [ ] Application button exists beside Edit in Job Detail Drawer
- [ ] Both navigate to `/jobs/{job_id}/application`
- [ ] Back navigation returns to Job context

### Application

- [ ] User can change application status
- [ ] User can enter Applied Date
- [ ] User can add/edit/delete follow-ups
- [ ] Follow-ups support date, note, completion

### Preparation

- [ ] Hard-skill recommendations are generated from existing Job/User intelligence
- [ ] Soft-skill recommendations are generated from existing Job/User intelligence
- [ ] Recommendations use Job + Company + User context where relevant
- [ ] Each recommendation explains Why / What / How
- [ ] Recommendations have priority
- [ ] Recommendations are actionable rather than generic

### Resume

- [ ] Tailored resume uses existing Resume analysis
- [ ] Tailored resume uses LinkedIn analysis
- [ ] Tailored resume uses existing User Skills and evidence
- [ ] Tailored resume uses existing Job analysis
- [ ] Tailored resume uses existing Company analysis where useful
- [ ] Generated resume is versioned
- [ ] User can view/edit/regenerate/download
- [ ] No fabricated information

### Cover Letter

- [ ] Uses existing Job intelligence
- [ ] Uses existing Company intelligence
- [ ] Uses existing User intelligence
- [ ] Uses relevant existing experience
- [ ] Is job-specific and company-specific
- [ ] Is versioned
- [ ] User can view/edit/regenerate/copy
- [ ] No fabricated information

### Architecture

- [ ] Existing intelligence is reused
- [ ] Existing analysis services are reused
- [ ] No duplicate analysis pipeline is introduced
- [ ] Existing design system is reused
- [ ] Existing architecture and naming conventions are preserved

---

## Final Implementation Rule

The Application Workspace is a **consumer of existing Career Intelligence**, not a replacement for it.

The implementation should follow:

```text
Existing Intelligence
        ↓
Application-specific reasoning
        ↓
Preparation recommendations
        ↓
Tailored Resume
        ↓
Cover Letter
        ↓
User reviews and edits
        ↓
Application
```

First inspect the repository and report:

1. What existing data can already be reused
2. What existing services/components can be reused
3. What is missing
4. The smallest set of backend/frontend changes required

Only then implement the feature.
