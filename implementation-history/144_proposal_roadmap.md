# Personalized Goal-Based Roadmap System

## 1. Overview

The Roadmap system is a personalized, goal-oriented system for helping users reach a specific outcome.

A Roadmap is not limited to Job Applications.

It can be:

- Generated from a Job Application
- Generated from a career or skill goal
- Created completely manually by the user

The core concept is:

> Goal → Required capabilities → Milestones → Tasks → Skills → Resources → Evidence → Progress

For the Job Search product, the primary flow is:

    Job
      ↓
    Application
      ↓
    Job + Company + User Intelligence
      ↓
    Skill Gap Analysis
      ↓
    Roadmap
      ↓
    Milestones
      ↓
    Tasks
      ↓
    Skills / Resources / Notes
      ↓
    Progress / Evidence

The Roadmap itself must remain an independent domain entity and must not be tightly coupled to the Application domain.

---

# 2. Product Goals

The Roadmap system should allow users to:

1. Create a roadmap for a specific job application.
2. Create a roadmap for a general career goal.
3. Create a roadmap for a specific skill.
4. Create a roadmap manually from scratch.
5. Let AI generate an initial roadmap.
6. Edit AI-generated roadmaps.
7. Add, remove, reorder, and edit milestones and tasks.
8. Track progress.
9. Add notes to milestones and tasks.
10. Add learning resources.
11. Record evidence of learning or practice.
12. Track skill progress.
13. Create new roadmap versions when the roadmap meaningfully changes.
14. Undo recent destructive actions.
15. Eventually share roadmaps with other people.

---

# 3. Core Product Principle

The Roadmap is a Goal → Path → Action → Evidence system.

    Goal
      ↓
    Required capabilities
      ↓
    Skills / knowledge / behaviors
      ↓
    Milestones
      ↓
    Tasks
      ↓
    Resources + Practice
      ↓
    Evidence
      ↓
    Progress
      ↓
    Goal readiness

The system should not primarily distinguish between Hard Skills and Soft Skills.

The important question is:

> What does the user need to learn, improve, practice, or demonstrate to achieve the goal?

Hard/Soft classification can remain metadata on the Skill entity, but it should not define the Roadmap structure or UI.

---

# 4. Roadmap Sources

Every Roadmap has a source.

Supported sources:

    APPLICATION
    AI_GENERATED
    MANUAL

## Application-generated Roadmap

Created from a Job Application.

    Application
        ↓
    Job Analysis
    Company Analysis
    User Analysis
    Skill Analysis
    Skill Gaps
    Existing Recommendations
        ↓
    AI
        ↓
    Roadmap

## AI-generated Roadmap

Created from a user-defined goal.

Example:

    Goal:
    Become a Senior Backend Engineer

## Manual Roadmap

Created completely by the user.

Example:

    Goal:
    Learn Kubernetes

    Milestone:
    Kubernetes Fundamentals

    Tasks:
    - Learn Pods
    - Learn Deployments
    - Learn Services

---

# 5. Relationship With Application

Application and Roadmap should be separate domains.

Recommended relationship:

    User
      │
      └── Roadmaps
            │
            ├── Job-specific Roadmap
            ├── Career Roadmap
            ├── Skill Roadmap
            └── Manual Roadmap

An Application can reference a Roadmap.

For MVP:

    Application
        │
        └── roadmap_id

The Roadmap must remain usable even if the Application is later archived.

The Roadmap should not depend on the Application to exist.

---

# 6. Goal Model

Every Roadmap must have a Goal.

Example:

    Goal Type:
    JOB

    Title:
    Become ready for Senior Backend Engineer at Company X

    Target Job:
    Senior Backend Engineer

    Target Company:
    Company X

Future Goal Types:

    JOB
    CAREER
    SKILL
    PROJECT
    CUSTOM

The Goal should be independent from the Roadmap structure.

---

# 7. Roadmap Structure

Conceptually:

    Roadmap
    │
    ├── Goal
    │
    ├── Versions
    │
    └── Nodes / Milestones
          │
          └── Tasks
                │
                ├── Skills
                ├── Resources
                ├── Notes
                └── Evidence

The UI can initially present this as a vertical journey.

The backend should support branching so that the system can evolve into a real roadmap graph.

---

# 8. Roadmap as a Graph

The Roadmap should support multiple paths.

Example:

                             Goal
                               │
                               ●
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              Backend Basics          Cloud Basics
                    │                     │
                    ▼                     ▼
                API Design               AWS
                    │                     │
                    └──────────┬──────────┘
                               ▼
                         System Design
                               │
                               ▼
                              Goal

This enables:

- Multiple parallel learning paths
- Prerequisites
- Converging paths
- Optional branches
- Different paths toward the same goal

The initial UI does not need to expose a full graph editor.

The data model should support it from the beginning.

---

# 9. Milestones

A Milestone represents a meaningful achievement.

Example:

    Milestone:
    Kubernetes Fundamentals

    Outcome:
    Understand and use the core Kubernetes primitives
    required for this role.

A Milestone can contain:

- Description
- Tasks
- Skills
- Resources
- Notes
- Progress
- Completion criteria
- Dependencies

Milestones should represent outcomes rather than simply topics.

Instead of:

    Kubernetes

Prefer:

    Kubernetes Fundamentals

Even better:

    Deploy and operate a basic containerized application on Kubernetes

---

# 10. Tasks

Tasks are concrete actions the user can perform.

Example:

    Milestone:
    Kubernetes Fundamentals

    Tasks:

    □ Learn Pods
    □ Learn Deployments
    □ Learn Services
    □ Deploy a FastAPI application
    □ Practice rolling updates

Each Task can contain:

- Title
- Description
- Status
- Priority
- Skill references
- Resources
- Notes
- Success criteria
- Estimated effort
- Due date (optional)

Task statuses:

    NOT_STARTED
    IN_PROGRESS
    COMPLETED
    SKIPPED

---

# 11. Skills

Skills remain global system entities.

A Roadmap references existing Skills instead of creating duplicate skill records.

Example:

    Task
      ↓
    Skill: Kubernetes

If the required Skill does not exist:

    Roadmap Generation
          ↓
    Required Skill
          ↓
    Skill exists?
       ├── Yes → reference existing Skill
       └── No  → create Skill

The system must avoid duplicate Skills.

Skill normalization and alias matching should remain part of the existing Skill system.

---

# 12. Skill Classification

Skills may contain metadata such as:

    skill_type:
    HARD
    SOFT
    DOMAIN
    TOOL
    TECHNOLOGY
    etc.

However, the Roadmap should not be divided into:

    Hard Skills
    Soft Skills

Instead, all relevant Skills can appear in one prioritized journey.

Example:

    1. System Design
    2. Kubernetes
    3. Technical Communication
    4. AWS
    5. Leadership

The ordering should be based on:

- Importance to the Goal
- Current Skill Gap
- Dependencies
- User readiness
- Priority
- Expected impact
- Estimated effort

---

# 13. Existing Intelligence Reuse

For Application-generated Roadmaps, the system should reuse existing intelligence.

## Job Intelligence

- Job description
- Responsibilities
- Requirements
- Preferred requirements
- Extracted Skills
- Seniority
- Experience requirements
- Job keywords
- Existing job score
- User/job match
- Existing Skill Gaps

## Company Intelligence

- Company information
- Industry
- Products/services
- Technology context
- Existing company analysis
- Relevant company Skills/context

## User Intelligence

- Resume
- Parsed resume data
- LinkedIn profile
- LinkedIn analysis
- Work experience
- Projects
- Education
- Certifications
- User Skills
- Skill proficiency
- Skill evidence

## Existing Analysis

- Skill matching
- Skill gaps
- Transferable Skills
- Missing Skills
- Existing recommendations
- Readiness / fit analysis

The LLM should not unnecessarily re-analyze raw information when structured intelligence already exists.

---

# 14. AI Roadmap Generation

Generation flow:

    Application
       ↓
    Collect Existing Intelligence
       ↓
    Build Application Context
       ↓
    Identify Goal
       ↓
    Identify Relevant Gaps
       ↓
    Prioritize Gaps
       ↓
    Build Dependencies
       ↓
    Generate Milestones
       ↓
    Generate Tasks
       ↓
    Attach Skills
       ↓
    Generate Resources / Practice Suggestions
       ↓
    Generate Success Criteria
       ↓
    Roadmap v1

The generated roadmap must be actionable.

Avoid:

    Learn Kubernetes
    Learn AWS
    Learn System Design

Prefer:

    Milestone:
    Kubernetes Fundamentals

    Tasks:
    - Learn Pods
    - Learn Deployments
    - Learn Services
    - Deploy a FastAPI application

    Success Criteria:
    Can deploy a containerized API and explain
    the purpose of Deployment and Service.

---

# 15. Roadmap Prioritization

The AI should not include every possible Skill Gap.

It should select the smallest meaningful set of improvements that can materially improve the user's readiness for the Goal.

Priority factors:

1. Explicit requirement
2. Importance to the target
3. Current user gap
4. Dependency
5. Impact
6. Feasibility
7. Estimated effort
8. Transferability

Priority levels:

    CRITICAL
    HIGH
    MEDIUM
    LOW

---

# 16. Notes

Notes should be contextual.

Primary location:

    Task
      └── Notes

Secondary location:

    Milestone
      └── Notes

Example:

    Milestone:
    Kubernetes Fundamentals

    Task:
    Learn Kubernetes Services

    My Notes:

    "ClusterIP is clear now.
    Still need to understand Ingress."

    Resources:
    - Kubernetes Documentation
    - User-added article

The initial version should not create a completely independent Notes application.

A future Notes Center can aggregate all Roadmap notes.

---

# 17. Resources

Users can attach Resources to Tasks or Milestones.

Resource fields:

    title
    url
    description
    type
    status
    created_by

Resource types:

    ARTICLE
    VIDEO
    COURSE
    BOOK
    DOCUMENTATION
    PROJECT
    OTHER

Resource status:

    PLANNED
    IN_PROGRESS
    COMPLETED

Users should be able to add their own resources.

AI-generated resources should be distinguishable from user-added resources.

---

# 18. Evidence

Evidence connects Roadmap activity back to the User Skill Profile.

Example:

    Skill:
    Kubernetes

    Evidence:
    - Completed Kubernetes course
    - Built deployment project
    - Added project to GitHub
    - Completed roadmap tasks
    - Added personal notes

Evidence can eventually affect:

    Skill Confidence
    Skill Proficiency
    Skill Readiness

This creates a feedback loop:

    Roadmap
       ↓
    Learning
       ↓
    Practice
       ↓
    Evidence
       ↓
    Skill Profile
       ↓
    Updated Intelligence
       ↓
    Better Roadmaps

---

# 19. Progress

Progress should exist at multiple levels.

    Task Progress
         ↓
    Milestone Progress
         ↓
    Roadmap Progress

Example:

    Roadmap:
    72%

    Milestone 1:
    100%

    Milestone 2:
    80%

    Milestone 3:
    25%

Progress should be calculated from meaningful completion states instead of being an arbitrary manually entered percentage.

---

# 20. Roadmap Versioning

Versioning represents meaningful Roadmap revisions.

Example:

    Roadmap v1
    AI-generated

          ↓

    User Progress
    New Evidence
    Updated Skills
    New Job Requirements

          ↓

    Roadmap v2
    AI Revised

Do not create a new version for every small user edit.

User edits modify the current working version.

Major revisions create new versions.

Example:

    v1 — Initial AI generation
    v2 — AI revision after progress
    v3 — Revised for new target

Version history should support:

- View
- Compare
- Restore

---

# 21. Undo

Undo should exist for recent destructive or structural actions.

Examples:

    Task deleted
    [ Undo ]

    Milestone removed
    [ Undo ]

    Task moved
    [ Undo ]

A complete Git-like undo/redo system is not required for MVP.

Recommended approach:

    Immediate changes
        ↓
      Undo

    Major Roadmap changes
        ↓
    Version History

---

# 22. Manual Roadmap Creation

Users must be able to create a Roadmap without an Application.

Example:

    My Roadmaps

    [ + Create Roadmap ]

    Goal:
    Become a Senior Backend Engineer

    [ Create ]

Then:

    Roadmap

    ├── + Add Milestone
    │
    └── + Add Task

Everything should be editable.

The user should be able to:

- Create milestones
- Create tasks
- Add Skills
- Add Resources
- Add Notes
- Set priorities
- Reorder nodes
- Create dependencies
- Track progress

AI should be optional.

---

# 23. UI Architecture

The Roadmap should feel like a visual journey rather than a traditional Todo List.

Recommended page structure:

    ┌──────────────────────────────────────────────────────────────────┐
    │ ← My Roadmaps                              + New Roadmap         │
    ├──────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  Goal                                                            │
    │  Become Senior Backend Engineer                       72%         │
    │                                                                  │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │                         ROADMAP                            │  │
    │  │                                                            │  │
    │  │                         ● Goal                              │  │
    │  │                           │                                │  │
    │  │                  ┌────────┴────────┐                       │  │
    │  │                  ▼                 ▼                       │  │
    │  │           ┌────────────┐    ┌────────────┐                 │  │
    │  │           │ ✓ Backend  │    │ ✓ Cloud    │                 │  │
    │  │           │   Basics   │    │   Basics   │                 │  │
    │  │           └─────┬──────┘    └──────┬─────┘                 │  │
    │  │                 │                  │                       │  │
    │  │                 └────────┬─────────┘                       │  │
    │  │                          ▼                                  │  │
    │  │                   ┌──────────────┐                          │  │
    │  │                   │ ◉ System     │                          │  │
    │  │                   │   Design     │                          │  │
    │  │                   └──────┬───────┘                          │  │
    │  │                          │                                  │  │
    │  │                          ▼                                  │  │
    │  │                         Ready                               │  │
    │  └────────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  [ + Add milestone ]    [ Edit roadmap ]    [ View history ]     │
    └──────────────────────────────────────────────────────────────────┘

---

# 24. Roadmap Node UI

Each Milestone should be visually distinct.

Collapsed:

    ┌─────────────────────────────────────┐
    │ ◉  SYSTEM DESIGN                    │
    │                                     │
    │    1 / 4 tasks completed            │
    │    ███████░░░░░ 25%                 │
    │                                     │
    │    Skills                           │
    │    • System Design                  │
    │    • Distributed Systems            │
    │                                     │
    │    [ View tasks → ]                 │
    └─────────────────────────────────────┘

Expanded:

    ┌─────────────────────────────────────┐
    │ SYSTEM DESIGN                       │
    │                                     │
    │ ✓ Learn caching                     │
    │   └─ 2 resources · 1 note           │
    │                                     │
    │ ◉ Study message queues              │
    │   └─ 3 resources · 2 notes          │
    │                                     │
    │ ○ Design scalable API               │
    │                                     │
    │ ○ Practice system design            │
    │                                     │
    │ [+ Add task]                        │
    └─────────────────────────────────────┘

---

# 25. Sidebar

A compact sidebar should provide context:

    ┌──────────────────┐
    │ ROADMAP          │
    │                  │
    │ 72% Complete     │
    │ █████████░░      │
    │                  │
    │ 4 / 6 Milestones │
    │ 12 / 18 Tasks    │
    │                  │
    │ ──────────────── │
    │ Goal             │
    │ Senior Backend   │
    │ Engineer         │
    │                  │
    │ Skills           │
    │ Kubernetes       │
    │ System Design    │
    │ AWS              │
    │                  │
    │ [ Edit Goal ]    │
    └──────────────────┘

---

# 26. Branching UI

The initial implementation can use a vertical Roadmap.

When branches exist:

                             ● Goal
                               │
                      ┌────────┴────────┐
                      ▼                 ▼
                 ● Backend         ● Cloud
                      │                 │
                      ▼                 ▼
                 ● API Design          ● AWS
                      │                 │
                      └────────┬────────┘
                               ▼
                        ● System Design

Users should be able to collapse branches.

This prevents large Roadmaps from becoming visually overwhelming.

---

# 27. Roadmap Interaction

## Milestones

Users can:

- Add
- Edit
- Delete
- Reorder
- Expand/collapse
- Mark complete
- Add dependencies

## Tasks

Users can:

- Add
- Edit
- Delete
- Reorder
- Mark in progress
- Mark complete
- Add notes
- Add resources
- Add Skills

## Roadmap

Users can:

- Edit Goal
- Rename Roadmap
- Edit description
- Add/remove nodes
- View progress
- View history
- Undo recent changes

---

# 28. Recommended Backend Domain Model

Conceptually:

    User
     │
     ├── Skills
     ├── SkillEvidence
     └── Roadmaps
           │
           ├── Roadmap
           │     ├── Goal
           │     ├── Versions
           │     └── Nodes
           │
           └── ...

Suggested entities:

    Roadmap
    RoadmapGoal
    RoadmapVersion
    RoadmapNode
    RoadmapEdge
    RoadmapTask
    RoadmapResource
    RoadmapNote
    RoadmapEvidence

Depending on the existing architecture, some entities can be simplified.

---

# 29. Roadmap Data Model

## Roadmap

    id
    user_id
    title
    description
    goal_type
    source
    application_id nullable
    status
    current_version_id
    created_at
    updated_at

Possible source values:

    APPLICATION
    AI_GENERATED
    MANUAL

Possible status values:

    ACTIVE
    COMPLETED
    ARCHIVED

---

# 30. Roadmap Goal

    id
    roadmap_id
    type
    title
    description
    target_job_id nullable
    target_company_id nullable
    target_skill_id nullable

---

# 31. Roadmap Version

    id
    roadmap_id
    version_number
    title
    description
    created_by
    created_at

Possible created_by values:

    AI
    USER
    SYSTEM

---

# 32. Roadmap Node

The Roadmap should use a graph-compatible model.

    id
    roadmap_version_id
    type
    title
    description
    position
    status
    priority
    parent_id nullable

Possible node types:

    GOAL
    MILESTONE
    TASK

If the project already has a dedicated Task entity, it should be reused rather than duplicated.

---

# 33. Roadmap Edge

    id
    roadmap_version_id
    source_node_id
    target_node_id
    type

Possible edge types:

    PREREQUISITE
    NEXT
    OPTIONAL

This enables branching and merging.

---

# 34. Roadmap Task

If Tasks require a dedicated entity:

    id
    roadmap_node_id
    description
    status
    priority
    estimated_effort
    success_criteria
    completed_at

---

# 35. Skill Relationship

    RoadmapNode
         │
         └── Skill references
                 │
                 ▼
               Skill

Do not duplicate Skill records inside Roadmaps.

Use the global Skill entity.

---

# 36. Resource Model

    RoadmapResource
    ├── id
    ├── node_id
    ├── title
    ├── url
    ├── description
    ├── type
    ├── status
    ├── source
    └── created_at

Possible source values:

    AI
    USER

---

# 37. Note Model

    RoadmapNote
    ├── id
    ├── node_id
    ├── user_id
    ├── title
    ├── content
    ├── created_at
    └── updated_at

Notes should primarily belong to Tasks or Milestones.

---

# 38. Evidence Model

    RoadmapEvidence
    ├── id
    ├── node_id
    ├── skill_id
    ├── type
    ├── title
    ├── description
    ├── url nullable
    ├── created_at
    └── user_id

Possible evidence types:

    PROJECT
    COURSE
    CERTIFICATION
    PRACTICE
    WORK
    NOTE
    RESOURCE
    OTHER

---

# 39. Skill Profile Integration

The Roadmap integrates with the existing Skill system.

Example:

    Roadmap Task
        ↓
    Kubernetes
        ↓
    User Skill Profile
        ↓
    Current Proficiency: Beginner
        ↓
    Task Completed
        ↓
    Evidence Added
        ↓
    Skill Confidence Updated

The Skill Intelligence system should remain responsible for calculating proficiency.

The Roadmap provides structured evidence and progress.

---

# 40. Application Integration

When creating a Roadmap from an Application:

    Application
        │
        ├── Job
        ├── Company
        ├── User
        ├── Job Analysis
        ├── Company Analysis
        ├── Skill Analysis
        └── Gap Analysis
                 │
                 ▼
          Roadmap Generator
                 │
                 ▼
             Roadmap v1

The Application can store:

    application.roadmap_id

The Roadmap should not depend on Application data to remain usable.

If the Application is archived, the Roadmap remains available.

---

# 41. API Concept

Basic Roadmap API:

    POST   /roadmaps
    GET    /roadmaps
    GET    /roadmaps/:id
    PATCH  /roadmaps/:id
    DELETE /roadmaps/:id

Generation:

    POST /roadmaps/:id/generate

Generate from Application:

    POST /applications/:id/roadmap

Milestones:

    POST   /roadmaps/:id/milestones
    PATCH  /milestones/:id
    DELETE /milestones/:id

Tasks:

    POST   /milestones/:id/tasks
    PATCH  /tasks/:id
    DELETE /tasks/:id

Notes:

    POST   /roadmap-nodes/:id/notes
    PATCH  /notes/:id
    DELETE /notes/:id

Resources:

    POST   /roadmap-nodes/:id/resources
    PATCH  /resources/:id
    DELETE /resources/:id

Versions:

    GET  /roadmaps/:id/versions
    POST /roadmaps/:id/revisions
    POST /roadmaps/:id/restore

---

# 42. AI Services

Recommended services:

    RoadmapGenerator
    RoadmapRecommender
    RoadmapRevisionService
    RoadmapProgressAnalyzer

## RoadmapGenerator

Creates the initial Roadmap.

## RoadmapRecommender

Suggests changes based on user progress.

## RoadmapRevisionService

Creates meaningful new Roadmap versions.

## RoadmapProgressAnalyzer

Analyzes completion and evidence and feeds relevant information back into Skill Intelligence.

---

# 43. AI Generation Context

For Application-based generation, create a structured context object.

Example:

    {
      "goal": {},
      "job": {},
      "company": {},
      "user": {},
      "skills": {},
      "skill_gaps": {},
      "existing_recommendations": {},
      "application_context": {}
    }

The AI output should also be structured.

Example:

    {
      "roadmap": {
        "title": "",
        "goal": {},
        "milestones": []
      }
    }

The generated output must be validated before persistence.

---

# 44. AI Accuracy Rules

The AI must not invent user experience.

The AI may:

- Organize existing information
- Recommend learning
- Generate practice exercises
- Generate success criteria
- Prioritize gaps
- Create a learning sequence

The AI must not:

- Invent work experience
- Invent projects
- Invent certifications
- Claim the user has a Skill without evidence
- Claim the user completed a Task
- Remove user-created Roadmap items without explicit user approval

---

# 45. User vs AI Ownership

Roadmap nodes should track their origin when useful.

Possible values:

    AI_GENERATED
    USER_ADDED
    USER_EDITED
    AI_REVISED

This is important when generating future Roadmap revisions.

AI revisions must preserve user-created content unless the user explicitly approves its removal.

---

# 46. Roadmap Revision UX

When AI proposes a new Roadmap:

    ┌─────────────────────────────────────────────┐
    │ New Roadmap Revision Available             │
    │                                             │
    │ Based on your progress, we recommend       │
    │ updating your Roadmap.                     │
    │                                             │
    │ Added                                       │
    │ + Kubernetes Production                    │
    │ + AWS ECS                                  │
    │                                             │
    │ Changed                                     │
    │ System Design → Advanced System Design     │
    │                                             │
    │ Removed                                     │
    │ - Kubernetes Basics                         │
    │                                             │
    │ [ Review Changes ]                          │
    └─────────────────────────────────────────────┘

The user explicitly approves the revision.

---

# 47. Sharing — Future Phase

Roadmaps should eventually support sharing.

Possible visibility:

    PRIVATE
    LINK_ONLY
    PUBLIC

Possible permissions:

    VIEW
    COMMENT
    EDIT

Example public view:

    My Career Roadmap

    Goal:
    Senior Backend Engineer

    Progress:
    72%

    ✓ Backend Fundamentals
    ✓ Kubernetes
    ◉ System Design
    ○ AWS

Sharing is not part of the first MVP.

---

# 48. MVP Scope

## Backend

- Roadmap
- Goal
- Milestone
- Task
- Skill references
- Notes
- Resources
- Progress
- Application relationship
- AI generation
- Basic source tracking

## Frontend

- My Roadmaps
- Roadmap detail page
- Goal header
- Visual milestone path
- Expand/collapse milestones
- Task management
- Notes
- Resources
- Progress
- Add/edit/delete
- Undo for recent destructive actions

## AI

- Generate Roadmap from Application
- Reuse existing Job/Company/User intelligence
- Generate prioritized milestones
- Generate actionable tasks
- Attach Skills
- Generate success criteria

---

# 49. Phase 2

Add:

- Roadmap versioning
- AI Roadmap revision
- Evidence
- Skill progress integration
- Dependency graph
- Branching Roadmap UI
- Compare revisions
- Restore previous version

---

# 50. Phase 3

Add:

- Advanced manual Roadmap builder
- AI-assisted Task creation
- AI suggestions while editing
- Goal recommendations
- Cross-Roadmap Skill tracking
- Resource recommendations
- Advanced progress analytics

---

# 51. Phase 4

Add:

- Roadmap sharing
- Public Roadmaps
- Private links
- Comments
- Collaboration
- Roadmap templates
- Clone Roadmap

---

# 52. Final Architecture

                              USER
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
           Profile            Skills           Roadmaps
              │                 │                  │
       Resume / LinkedIn        │          ┌───────┴────────┐
              │                 │          │                │
              └────────────┬────┘       Job Roadmap     Manual Roadmap
                           │                │
                           ▼                ▼
                    USER INTELLIGENCE   Career Goal
                           │                │
                           └───────┬────────┘
                                   │
                                   ▼
                              APPLICATION
                                   │
                     ┌─────────────┼─────────────┐
                     │             │             │
                    JOB         COMPANY         USER
                     │             │             │
                     └─────────────┼─────────────┘
                                   │
                             Skill / Gap Analysis
                                   │
                                   ▼
                            ROADMAP GENERATOR
                                   │
                                   ▼
                               ROADMAP V1
                                   │
                          ┌────────┴────────┐
                          ▼                 ▼
                     MILESTONES          BRANCHES
                          │                 │
                          ▼                 │
                        TASKS ◄─────────────┘
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
             SKILLS    RESOURCES    NOTES
               │
               ▼
            EVIDENCE
               │
               ▼
         SKILL PROGRESS
               │
               ▼
      UPDATED USER INTELLIGENCE
               │
               ▼
       AI REVISION PROPOSAL
               │
               ▼
            ROADMAP V2

---

# 53. Core Design Decisions

The implementation should preserve these principles:

1. Roadmap is an independent domain entity.
2. Application is one source of Roadmaps, not their owner.
3. Every Roadmap has a Goal.
4. Roadmaps can be manually created.
5. Roadmaps can be AI-generated.
6. AI-generated Roadmaps are fully editable by users.
7. Hard and Soft Skills are not separate Roadmap sections.
8. Skills are global entities and are referenced by Roadmap nodes.
9. Missing Skills should be added to the global Skill system.
10. Roadmaps prioritize Skills based on Goal relevance, not Skill type.
11. Milestones represent meaningful outcomes.
12. Tasks represent concrete actions.
13. Notes and Resources belong to contextual nodes.
14. Evidence connects Roadmap activity back to the Skill Profile.
15. The data model supports branching and merging.
16. The initial UI can remain a simple vertical journey.
17. Undo is for immediate changes; versioning is for meaningful revisions.
18. AI must reuse existing intelligence rather than re-analyzing everything.
19. User-created content must be preserved during AI revisions.
20. Sharing can be added later without changing the core Roadmap model.

---

# 54. Recommended Implementation Order

    1. Roadmap domain model
            ↓
    2. Goal
            ↓
    3. Milestone
            ↓
    4. Task
            ↓
    5. Skill relationships
            ↓
    6. Manual Roadmap CRUD
            ↓
    7. Roadmap UI
            ↓
    8. Application → Roadmap generation
            ↓
    9. Notes + Resources
            ↓
    10. Progress
            ↓
    11. Undo
            ↓
    12. Evidence
            ↓
    13. Versioning
            ↓
    14. AI Revision
            ↓
    15. Branching Graph
            ↓
    16. Sharing

---

# 55. Final Product Vision

The long-term Roadmap system should become a reusable personal career-development engine.

The Job Application is only one entry point.

The complete system should eventually support:

    Job
    Career
    Skill
    Project
    Learning Goal
    Custom Goal

All of them use the same underlying model:

    Goal
      ↓
    Roadmap
      ↓
    Milestones
      ↓
    Tasks
      ↓
    Skills
      ↓
    Resources
      ↓
    Notes
      ↓
    Evidence
      ↓
    Progress
      ↓
    Updated User Intelligence
      ↓
    Better Future Recommendations

This architecture allows the initial product to solve the immediate problem of preparing a user for a specific Job Application while keeping the Roadmap system independent enough to become a general-purpose personalized career and learning system later.
