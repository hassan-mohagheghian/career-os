# State Management

All AI workflows use LangGraph's native state management. Nodes communicate exclusively through State — never through temporary files.

## Architecture

Input → LangGraph State → Node A → Updated State → Node B → Final Output

## State Models

| Workflow | State Model | Fields |
|----------|-------------|--------|
| Job Processing | `JobProcessingState` | raw_content, job_title, company, scores, extraction_data, structured_data, summary_data, resume_text, linkedin_text, rules |
| Company Processing | `CompanyProcessingState` | raw_content, company_name, company_type, extraction_data, intelligence_data, scores, company_id |
| Insights | `InsightsState` | section, section_data, all_results, errors_list |
| Skill Roadmap | `SkillRoadmapState` | skill_name, job_type, job_id, items, version, session_id, provider_name |

## State Lifecycle

1. **Creation**: `create_initial_state()` factory
2. **Mutation**: Nodes return new/updated state dicts
3. **Checkpointing**: Automatic via LangGraph checkpointer
4. **Completion**: Final state contains output in `output` field

## Key Principles

- Nodes never write/read temporary files
- State is strongly typed via TypedDict/Pydantic
- Checkpointing uses LangGraph native mechanisms
- Only final business artifacts are persisted to DB
