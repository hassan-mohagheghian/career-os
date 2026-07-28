You are a senior product architect, AI engineer, backend engineer, frontend engineer, and technical documentation specialist.

Your task is to redesign and implement a new version of the existing:

Insights → Skills

feature inside the current project.

This is a major product evolution, not an isolated page.

The feature must integrate naturally with the existing product architecture, domain model, database, AI pipelines, prompts, tools, UI design system, naming conventions, and existing workflows.

You have full permission to inspect the entire repository and refactor related areas when required.

Do not start coding immediately.

First understand the existing system, create the required project knowledge documentation, analyze the current implementation, then propose an implementation plan.

---

# Product Context

Current product navigation:


Jobs
Companies
Skills

Insights
├── Overview
├── Skills
├── Opportunities
├── Companies
└── Market

Networking
Settings

Resume
Rules


The target feature:


Insights → Skills


should become the intelligence center connecting:


Jobs
↓
Market Skill Intelligence
↓
User Skill Profile
↓
Skill Gap Analysis
↓
Recommendations
↓
Learning Roadmap
↓
Skills Knowledge Base


---

# Phase 0 — Project Understanding Documentation

Before implementing anything, analyze the repository and create/update a portable project understanding document.

The purpose:

Another AI agent, developer, or architect should be able to read this document and understand the project without access to the repository.

This document is the "project brain".

---

## Create:


docs/PROJECT_CONTEXT.md


If a similar document already exists:

- Analyze it.
- Improve it.
- Update outdated information.
- Keep useful existing content.

---

# PROJECT_CONTEXT.md Requirements

The document must include:

## 1. Project Overview

Document:

- Project name
- Product purpose
- Target users
- Main problems solved
- Core workflows


---

## 2. Product Structure

Explain current product areas:

- Jobs
- Companies
- Skills
- Insights
- Networking
- Settings
- Resume
- Rules


For each area explain:

- Responsibility
- Main features
- Important files/modules


---

## 3. Technology Stack

Document:

Frontend:

- Framework
- Language
- UI framework
- State management
- Data fetching
- Component architecture


Backend:

- Framework
- Language
- Architecture style
- Main libraries


Database:

- Database engine
- Main entities
- Relationships


Infrastructure:

- Deployment
- CI/CD
- Cloud
- Monitoring


---

## 4. Architecture Summary

Document:

- System architecture
- Layers
- Components
- Data flow
- Communication patterns

Include Mermaid diagrams when useful.

---

## 5. Domain Model

Document important business concepts:

Examples:

- Job
- Company
- Skill
- User Profile
- Resume
- LinkedIn Profile
- Rule
- Recommendation
- Roadmap
- Insight

Explain:

- Relationships
- Business rules
- Important constraints


---

## 6. AI Architecture

Document:

- Existing AI agents
- Existing prompts
- AI tools
- Workflows
- Data extraction pipelines
- Evaluation mechanisms


Explain how future AI features should be added.


---

## 7. Development Rules

Document:

- Coding conventions
- Folder structure rules
- Naming conventions
- Architecture constraints
- Testing rules
- Patterns to follow
- Patterns to avoid


---

## 8. Current Feature Map

Document:

Existing features:

- Location in code
- Main modules
- Current behavior
- Limitations


---

## 9. AI Agent Instructions

Create instructions for future AI agents:

Before changing code:

1. Understand existing architecture.
2. Search for existing abstractions.
3. Avoid duplicate concepts.
4. Follow existing naming.
5. Preserve boundaries.
6. Add tests.
7. Update documentation.


---

## 10. Technical Debt

Document:

- Existing problems
- Refactoring opportunities
- Known limitations


---

# Phase 1 — Existing System Analysis

Analyze the current implementation.

Inspect:

## Frontend

Analyze:

- Routing
- Insights pages
- Components
- Charts
- Tables
- Design system
- State management
- API integration


Identify:

- Existing reusable components
- Existing skill-related UI
- Current naming conventions


---

## Backend

Analyze:

- APIs
- Services
- Domain models
- Database models
- Jobs pipeline
- Company pipeline
- Resume processing
- LinkedIn processing
- Skill extraction logic
- AI integration


---

## Database

Identify existing models:

- jobs
- companies
- skills
- users
- resumes
- profiles
- rules
- scoring
- recommendations


Document relationships.


---

# Phase 2 — Feature Goal

Rebuild Insights → Skills into a complete Skill Intelligence system.

The system must:

1. Analyze existing jobs.
2. Analyze companies.
3. Extract market-required skills.
4. Normalize skills.
5. Compare market skills with user skills.
6. Calculate strengths and gaps.
7. Generate recommendations.
8. Update the global skill database.
9. Provide roadmap generation.

---

# Phase 3 — Domain Design

Design or improve these concepts.

## Skill

A skill should support:


Skill

name
aliases
category
description
market demand
frequency
related skills
seniority relevance
evidence

---

## Skill Evidence

Every skill should have evidence.

Sources:

- Job postings
- Companies
- Resume
- LinkedIn
- Projects


Example:


Python

Market demand:
92%

Evidence:

140 jobs
25 companies
User experience: 9 years

---

## User Skill Assessment

Example:


Python

Required:
Expert

User:
Advanced

Confidence:
0.91

Evidence:

Backend experience
FastAPI projects
Production systems

---

## Skill Gap

Represent:

Market requirement vs user level.

Example:


Kubernetes

Market:
Advanced

User:
Beginner

Gap:
High priority


---

# Phase 4 — AI Pipeline

Analyze all existing prompts.

For each prompt:

Determine:

- Reuse?
- Update?
- Replace?
- New prompt needed?


Create/update AI workflows.

---

# Required AI Agents

## 1. Market Skill Extraction Agent

Input:

- Jobs
- Companies


Output:

Structured skills:

```json
{
 "skill": "Kubernetes",
 "category": "Infrastructure",
 "frequency": 50,
 "importance": "high",
 "related_skills": [
   "Docker",
   "AWS"
 ]
}
2. User Skill Assessment Agent

Input:

Resume
LinkedIn
Experience
Projects

Output:

Structured user skills.

3. Skill Gap Analysis Agent

Compare:

Market demand

against:

User profile

Generate:

Strengths
Missing skills
Priorities
4. Roadmap Generation Agent

Generate:

Personalized learning paths.

Example:

Phase 1:
PostgreSQL optimization

Phase 2:
Kubernetes

Phase 3:
Distributed Systems
Phase 5 — Prompt Architecture

Analyze current prompt storage.

Follow existing architecture.

If required, refactor.

Possible structure:

prompts/

skills/
 ├── market_analysis.prompt
 ├── extraction.prompt
 ├── gap_analysis.prompt
 └── roadmap_generation.prompt

resume/
 └── skill_assessment.prompt

Do not create duplicate prompt systems.

Phase 6 — AI Tools

Analyze existing tools.

Create missing tools if required.

Required capabilities:

Skill Extraction Tool

Input:

Jobs / Companies

Output:

Normalized skills

Skill Matching Tool

Input:

User skills + Market skills

Output:

Gap analysis

Skill Merge Tool

Handle:

Python
python
Python 3

as one skill.

Roadmap Tool

Generate:

Learning roadmap.

All tools must follow existing architecture.

Phase 7 — Skills Knowledge Base Update

The analysis pipeline should update the global Skills system.

Root menu:

Skills

becomes the skill management center.

Support:

Add skills
Remove skills
Edit skills
Merge skills
Manage aliases
Manage categories
Review discovered skills
View market evidence
Create/edit/refine roadmaps
Phase 8 — Insights → Skills UI

Design the new page.

Include:

Overview Cards

Examples:

Total Skills Analyzed
Market Skills
User Strengths
Skill Gaps
High ROI Skills
Market Demand Charts

Examples:

Top skills:

Python
SQL
Docker
Kubernetes
Skill Gap Matrix

Columns:

Skill
Market Demand
User Level
Gap
Priority
Skill Categories

Examples:

Backend
Cloud
AI
Database
Frontend
Architecture
Recommendations

Example:

"Learn Kubernetes because 45% of target jobs require it and your current level is beginner."

Roadmap Preview

Show:

Current phase
Next skills
Estimated effort
Phase 9 — Compatibility Requirements

The implementation must:

Follow current design language.
Reuse existing components.
Respect current architecture.
Avoid duplicate models.
Preserve existing features.
Refactor where necessary.

Before creating anything new:

Search for existing equivalents.

Phase 10 — Implementation Plan

Before coding, provide:

Current architecture analysis.
Existing relevant files.
Database changes.
Backend changes.
Frontend changes.
AI prompt changes.
New AI tools.
Migration strategy.
Implementation phases.
Final Quality Requirement

The final result should feel like a natural evolution of the existing product.

It should create a complete intelligence loop:

Jobs
 ↓
Market Skills
 ↓
User Skills
 ↓
Skill Gap
 ↓
Recommendations
 ↓
Roadmap
 ↓
Skill Knowledge Base

The implementation should support both humans and AI agents as first-class users of the system.
