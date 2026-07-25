refactor_company_process_and_its_score

Improve the company processing workflow and company scoring system.

The goal is to create a dedicated Company Intelligence pipeline that processes company information from user-provided notes and links, extracts useful insights, calculates company scores, and displays the results clearly in the frontend.

---

# Backend Changes

## 1. Company Processing Input

Keep the current company creation/input workflow.

A company can be added using:
- User notes
- Company description
- URLs/links related to the company

The processing pipeline should use all available information.

Input sources:

- User-provided notes
- Company URLs
- Existing extracted company information (if available)


---

## 2. Company Information Extraction

During company processing:

If URLs are provided:

- Try to fetch and extract useful information from those links.
- Combine extracted information with user notes.
- Use all available context to build a complete company profile.

Extract relevant information such as:

### Company Overview
- Company name
- Industry/domain
- Product description
- Business model
- Headquarters/location
- Countries of operation
- Company size (if available)
- Funding/revenue signals (if available)

### Engineering & Work Environment
- Engineering culture
- Technology stack
- Engineering team information
- Technical blog/open-source activity
- Backend/platform focus
- Development practices

### Career & Relocation Information
- Visa sponsorship signals
- International hiring
- Remote/hybrid policy
- Language requirements
- Relocation support

### Company Reputation & Growth
- Product maturity
- Market position
- Growth signals
- Career opportunities
- Potential risks


The final processed company profile should be stored separately from the original user notes.

---

# 3. Company Scoring

Use only:

- Shared Rules
- Company Rules


Do NOT use Job Rules.

Generate only these three company scores:

## company_fit_score

Measures:
"How well does this company match my technical background and career direction?"

Based on:
- Engineering culture
- Technology alignment
- Product/domain relevance
- Backend/distributed systems opportunities
- Growth opportunities


---

## company_success_score

Measures:
"How likely am I to successfully join this company?"

Based on:
- Visa sponsorship
- Location
- International hiring
- English environment
- Remote/hybrid options
- Hiring accessibility


---

## company_overall_score

Calculate the final company score.

Recommended formula:

company_overall_score =
(company_fit_score * 0.5) +
(company_success_score * 0.5)


The overall score should be the main company ranking score.

---

# Frontend Changes

## Company Drawer Improvements

In the company drawer, organize information into tabs.

Keep the existing basic company information section at the top:

- Company name
- Location
- Industry
- Initial notes
- URLs

Improve only if necessary.


Add tabs:

---

## Tab 1: Original Notes

Show the original user input.

Features:

- Add notes
- Edit notes
- Delete notes
- Add/remove URLs
- Trigger reprocessing after changes


The original input must always remain editable.

---

## Tab 2: Company Intelligence

Show processed company information:

Sections:

- Company overview
- Product/business
- Engineering culture
- Technology stack
- Work environment
- Visa and relocation signals
- Growth opportunities
- Risks and concerns


---

## Tab 3: Scores

Display:

- Company Fit Score
- Company Success Score
- Company Overall Score


Also show:

- Score grade (A++, A+, A, B, C, D)
- Short explanation of why the score was given
- Main positive factors
- Main negative factors


---

# Job Drawer Integration

When a processed job is linked to a company:

Add a Company tab inside the Job drawer.

This tab should display:

- Company basic information
- Company Intelligence summary
- Company scores:
  - Fit Score
  - Success Score
  - Overall Score

The job drawer should combine:

Job information +
Job scores +
Linked company intelligence


---

# Processing Workflow

Expected flow:

User adds company:
        |
        v
Notes + URLs
        |
        v
Company processing pipeline
        |
        v
Extract company intelligence
        |
        v
Apply Shared Rules + Company Rules
        |
        v
Generate:
- company_fit_score
- company_success_score
- company_overall_score
        |
        v
Display in company drawer


---

# Requirements

- Do not remove existing company input functionality.
- Preserve original notes separately from AI-generated information.
- Make company processing repeatable after notes/URLs changes.
- Keep company scoring independent from job scoring.
- Reuse the existing rule engine architecture.
- Keep frontend consistent with the existing Jobs UI patterns.
- Make the design scalable for future company intelligence features.
