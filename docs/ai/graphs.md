# Graph Reference

## Job Processing Graph

**Name**: `job_processing`
**Entry**: `validate_input`
**Finish**: `completion_event`

```
START → validate_input → fetch_url → fallback_to_notes → extract_raw_content
      → clean_content → extract_structured_data → analyze_job → extract_skills
      → score_job → generate_summary → persist_results → completion_event → END
```

**Typed Output**: `JobAnalysisOutput`
**Retry Nodes**: `extract_raw_content`, `score_job`

## Company Processing Graph

**Name**: `company_processing`
**Entry**: `validate_input`
**Finish**: `completion_event`

```
START → validate_input → fetch_content → extract_company_data
      → analyze_company → score_company → save_results → completion_event → END
```

**Typed Output**: `CompanyAnalysisOutput`
**Retry Nodes**: `extract_company_data`, `analyze_company`

## Resume Generation Graph

**Name**: `resume_generation`
**Entry**: `load_resume`
**Finish**: `completion_event`

```
START → load_resume → load_job_context → tailor_content
      → format_output → validate_output → completion_event → END
```

**Typed Output**: `ResumeOutput`

## Cover Letter Generation Graph

**Name**: `cover_letter_generation`
**Entry**: `load_resume`
**Finish**: `completion_event`

```
START → load_resume → load_job_context → generate_cover_letter
      → format_output → validate_output → completion_event → END
```

**Typed Output**: `CoverLetterOutput`

## Skill Extraction Graph

**Name**: `skill_extraction`
**Entry**: `load_jobs`
**Finish**: `completion_event`

```
START → load_jobs → extract_skills → categorize_skills
      → enrich_skills → completion_event → END
```

**Typed Output**: `SkillExtractionOutput`

## Skill Roadmap Graph

**Name**: `skill_roadmap`
**Entry**: `load_current_skills`
**Finish**: `completion_event`

```
START → load_current_skills → load_market_data → analyze_gaps
      → generate_roadmap → prioritize → completion_event → END
```

**Typed Output**: `SkillRoadmapOutput`

## Career Insights Graph

**Name**: `insights_generation`
**Entry**: `overview`
**Finish**: `aggregate`

```
START → overview → skills → market → companies
      → networking → opportunities → aggregate → END
```

**Typed Output**: `CareerInsightsOutput`
**Retry Nodes**: All section nodes (1 retry each)

### Child Graphs (independently executable)

| Graph | Entry | Finish |
|-------|-------|--------|
| `insights_overview` | `collect_data` | `generate_summary` |
| `insights_skills` | `load_skills` | `generate_recommendations` |
| `insights_market` | `analyze_demand` | `generate_report` |
| `insights_companies` | `load_companies` | `generate_shortlist` |
| `insights_networking` | `analyze_connections` | `generate_recommendations` |
| `insights_opportunities` | `load_opportunities` | `generate_action_plan` |

## Generate All Graph

**Name**: `generate_all`
**Entry**: `job_processing`
**Finish**: `completion_event`

```
START → job_processing → company_processing → resume_generation
      → cover_letter_generation → skill_extraction → skill_roadmap
      → insights_generation → completion_event → END
```

**Typed Output**: Aggregated dict with all stage results
**Retry Nodes**: All stage nodes (1 retry each)

## Adding a New Graph

1. Create `apps/backend/ai/infrastructure/graphs/{name}/graph.py`
2. Implement `build_{name}_graph() -> GraphBuilder`
3. Add typed output model to `runtime/state.py`
4. Register in `graphs/__init__.py`
5. Add prompts to `prompts/{name}/`
6. Write tests in `tests/ai/infrastructure/graphs/`
