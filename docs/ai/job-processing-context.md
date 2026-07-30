# Job Processing Context

## Purpose

Defines the complete context provided to the AI processing pipeline for job analysis.

The context combines job data, resources, rules, and AI configuration into a structured input.

---

## Context Sources

The context is built from:

- Job entity
- Job resources
- Processing rules
- Scoring rules
- LLM configuration
- Prompt metadata
- Schema metadata

---

## Context Structure

The context contains:

- job
- resources
- rules
- llm_configuration
- prompt_version
- schema_version

---

## Job Data

The job data may include:

- Title
- Description
- Company
- Location
- Employment type
- Required skills
- Technologies
- Salary information

---

## Resources

Resources represent external information sources.

Supported resource types:

- PRIMARY_URL
- REFERENCE_URL
- NOTE

Each resource contains:

- type
- title
- content
- source_url

---

## Rules

The AI context includes the active scoring rules required for job evaluation.

Currently the context contains:

- Shared scoring rules
- Job scoring rules

These rules are evaluated together to produce three independent scores:

- Fit Score
- Success Score
- Overall Score

The Overall Score is **not** calculated from the Fit and Success scores. Instead, it is independently evaluated by the LLM using the complete set of applicable scoring rules and the overall job context.

Future versions may introduce additional rule groups (such as Recommendation, Validation, or Workflow rules), but the current implementation uses scoring rules only.

---

## Versioning

The context should include:

- Prompt version
- JSON schema version
- Processing workflow version

This allows reproducibility and debugging.
