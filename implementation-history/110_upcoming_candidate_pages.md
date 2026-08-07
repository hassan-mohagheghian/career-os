# Candidate Experience Redesign

## Replace Legacy Candidate & Roadmap Experience

## Architecture First

# Goal

Completely redesign the Candidate experience so it becomes one of the core modules of the platform.

This redesign must align with the current architecture and existing domains:

- Jobs
- Companies
- Skills
- Processing
- AI Workflows

The current implementation has evolved incrementally.

The goal is to make it:

- Consistent
- Extensible
- Domain-driven
- UX-first
- Future-proof

The implementation should include:

- Architecture review
- Backend
- Frontend
- Database
- Documentation
- Wireframes
- Mermaid diagrams
- Migration strategy
- Tests

If necessary, split implementation into multiple Implementation Histories.

Never try to implement everything in one phase.

---

# Step 0

## Read Existing System First

Before making any changes:

Read all existing documentation.

Inspect the existing implementation.

Especially review:

- Candidate
- Resume
- LinkedIn
- Skills
- Companies
- Jobs
- ProcessingExecution
- Matching
- Existing Roadmap
- LangGraph
- AI Workflows
- Current frontend structure
- Current navigation
- Current UX

The redesign MUST stay consistent with the existing system.

Do NOT redesign unrelated modules.

---

# Migration Rules

If an old Candidate implementation exists:

Review it.

Reuse what is good.

Refactor what is weak.

Remove obsolete implementations.

If an old Roadmap implementation exists:

Completely remove it.

Remove:

- pages
- APIs
- services
- workflows
- tests
- documentation

There must only be ONE Roadmap implementation.

The new implementation becomes the canonical one.

---

# Product Vision

This product is NOT an LMS.

It does NOT teach users.

It should:

Understand the market

↓

Understand the candidate

↓

Find missing skills

↓

Generate learning plans

Learning resources, tutorials and AI coaching are future features.

Do NOT implement those now.

---

# Candidate Philosophy

Candidate should answer four questions.

1.

Who am I?

↓

Dashboard

2.

What do I already know?

↓

Skills

Experience

Projects

3.

What am I missing?

↓

Gap Analysis

4.

What should I learn next?

↓

Roadmaps

---

# Candidate Module

Candidate becomes a Feature Module.

Structure:

Candidate

├── Profile Import
├── Dashboard
├── Sources
├── Skills
├── Experience
├── Projects
├── Gap Analysis
└── Roadmaps

Every page should have:

- documentation
- ASCII wireframe
- Mermaid diagrams
- UX description
- component hierarchy

---

# Candidate Domain

Candidate contains:

- Profile
- Sources
- Skills
- Experience
- Projects

Roadmaps are NOT part of Candidate.

Relationship:

Candidate

↓

Gap Analysis

↓

Learning Roadmap

A candidate may own multiple Roadmaps.

---

# Phase 1

# Candidate Profile Import

Highest priority.

This page becomes the first Candidate page.

Purpose:

Import professional information.

Supported inputs:

Required

- Resume

- LinkedIn

Optional

- GitHub

Future placeholders

- Portfolio
- StackOverflow
- Kaggle
- Behance
- Dribbble

Only Resume and LinkedIn should be implemented.

GitHub should exist as Optional.

Portfolio and others remain placeholders.

The page should support:

Upload Resume

Paste LinkedIn

GitHub Username

Analyze Profile

Replace Resume

Re-import LinkedIn

Required outputs:

ASCII Wireframe

Mermaid User Flow

Mermaid Component Diagram

UX documentation

---

# AI Profile Analysis

After Analyze:

Resume

↓

LinkedIn

↓

GitHub (optional)

↓

Extract

Skills

Experience

Projects

Target Role

↓

Candidate Review

↓

Create Candidate

---

# Candidate Review Page

Before storing:

Display:

Skills

Experience

Projects

Sources

Target Role

Summary

Allow:

Confirm

Cancel

Required:

ASCII Wireframe

Mermaid Flow

---

# Phase 2

# Candidate Dashboard

Purpose:

Provide an overview.

Display:

Profile Completeness

Current Target Role

Connected Sources

Quick Statistics

Roadmap Summary

Gap Summary

Job Match Summary

Recent Activity

Top Skills Preview

Recent Projects Preview

Dashboard becomes the landing page.

Required:

ASCII Wireframe

Mermaid Flow

Mermaid Component Tree

UX documentation

---

# Phase 3

# Candidate Sources

Purpose:

Manage imported sources.

Display:

Resume

LinkedIn

GitHub

Portfolio

Each source should display:

Version

Status

Last Updated

Replace

Re-import

Connect

Disconnect

Required:

ASCII Wireframe

Mermaid Diagram

---

# Phase 4

# Candidate Skills

Purpose:

Display Candidate Skills.

NOT Skill Catalog.

Display:

Explicit Skills

AI Inferred Skills

Confidence

Evidence

Source

Verification Status

Support:

Search

Filter

Sort

Future:

Merge

Approval

Manual Edit

Roadmaps MUST NOT appear here.

Required:

ASCII Wireframe

Mermaid Diagram

---

# Phase 5

# Candidate Experience

Display:

Company

Role

Dates

Description

Evidence

Future:

Merge Experience

Required:

Wireframe

Mermaid

---

# Phase 6

# Candidate Projects

Display:

Projects

Description

Used Skills

Evidence

Required:

Wireframe

Mermaid

---

# Phase 7

# Gap Analysis

Purpose:

Compare Candidate against Target Role.

Display:

Matched Skills

Missing Skills

Priority

Confidence

Future:

Learning Effort

Not now.

Required:

ASCII Wireframe

Mermaid Flow

---

# Phase 8

# Learning Roadmaps

Completely replace old Roadmap.

Roadmap is NOT a course.

It is Skill Progression.

Example:

Backend Engineer

↓

Python

↓

Git

↓

SQL

↓

FastAPI

↓

Docker

↓

Redis

↓

Celery

↓

PostgreSQL

↓

Kubernetes

Each node is a Skill.

NOT lessons.

NOT videos.

NOT tutorials.

---

# Roadmap Features

Each roadmap supports:

Progress

Completed Skills

Current Step

Expand

Extend

Regenerate

Delete

Version History

---

# Expand

Break roadmap into finer skills.

Example:

Docker

↓

Images

↓

Containers

↓

Volumes

↓

Networking

↓

Compose

---

# Extend

Continue roadmap after its ending.

Example:

Backend

↓

AWS

↓

Terraform

↓

Kafka

↓

System Design

---

# Future

Do NOT implement:

Courses

Videos

Exercises

Learning Resources

AI Tutor

Those belong to future phases.

---

# Skill Architecture

Keep Skill Catalog separated.

Skill Catalog

↓

Candidate Skills

↓

Gap Analysis

↓

Roadmaps

Candidate never creates new canonical skills directly.

Candidate references canonical skills.

---

# UX Rules

Every page must include:

Purpose

Goals

Actions

States

Loading

Empty

Error

Success

Responsive behavior

Navigation

---

# Documentation Rules

Every page MUST include:

ASCII Wireframe

Mermaid Diagram

Component Hierarchy

User Flow

State Diagram (where applicable)

Do NOT document pages using text only.

---

# Backend

Review existing APIs.

Reuse endpoints when possible.

Avoid duplication.

Keep architecture aligned with existing domains.

---

# Frontend

Reuse existing layout.

Reuse component library.

Keep visual consistency.

Only improve Candidate experience.

---

# Events

Emit:

candidate.created

candidate.updated

candidate.source.updated

candidate.skill.updated

candidate.review.completed

gap.analysis.generated

roadmap.created

roadmap.expanded

roadmap.extended

roadmap.completed

---

# Tests

Implement tests for:

Profile Import

Candidate Review

Dashboard

Sources

Skills

Experience

Projects

Gap Analysis

Roadmaps

Roadmap Expansion

Roadmap Extension

Migration

---

# Deliverables

Before implementation:

1. Architecture Review

2. Existing System Review

3. Migration Strategy

4. Phase Planning

For every phase:

Goal

Scope

Dependencies

Affected Files

Risks

Then implement:

Backend

Frontend

Documentation

Wireframes

Mermaid diagrams

Tests

Prioritize:

Architecture correctness

Domain consistency

UX consistency

Future extensibility

over implementation speed.
