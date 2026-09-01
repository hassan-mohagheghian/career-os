# Prompt 205+206 - Multi-Tenancy (user_id schema + scoped queries)

## Objective

Make all assets belong to a user. Add `user_id` columns to all aggregate root tables, update all repository constructors to accept `user_id`, update DI factories to extract current user from JWT, and scope all repository queries by `user_id`.

## Current State

- Auth system working (backend + frontend)
- All aggregate root tables lack `user_id` columns
- All repositories query without user scoping
- DI factories don't pass user context

## Phase 3: Schema Changes (Migration)

Alembic migration `multi_001` adds `user_id` (String(36), NOT NULL, indexed) to:
- job.jobs, company.companies, skill.skills, candidate.candidates
- application.applications, roadmap.roadmaps, placeholders.placeholders
- ai.llm_configurations, shared.rules, city.cities

Backfills all existing data to default user `hassan`.

Unique constraints updated:
- `shared.rules`: (category, key) → (category, key, user_id)
- `city.cities`: (city, country) → (city, country, user_id)
- `placeholders.placeholders`: PK (key) → PK (key, user_id)

## Phase 4: Repository + DI Changes

### Repositories
Each aggregate root repository constructor gains `user_id: str` parameter.
Query methods add `.filter(Model.user_id == self._user_id)`.

### DI Layer (dependencies.py)
- `get_current_user` imported from auth router
- All `get_*_repo` factories gain `current_user: User = Depends(get_current_user)` parameter
- Pass `current_user.id` to repository constructor

### Inline Routes (root_router.py)
- Import `get_current_user` and use `Depends(get_current_user)` in protected inline routes
- Pass `current_user.id` where needed

## Files Modified

### Models (add user_id column)
- `jobs/infrastructure/models/job_model.py`
- `companies/infrastructure/models/company_model.py`
- `skills/infrastructure/models/skill_model.py`
- `candidates/infrastructure/models/candidate_model.py`
- `applications/infrastructure/models/application_model.py`
- `roadmaps/infrastructure/models/roadmap_model.py`
- `placeholders/infrastructure/models/placeholder_model.py`
- `ai/infrastructure/models/llm_configuration_model.py`
- `rules/infrastructure/models/rule_model.py`
- `cities/infrastructure/models/city_model.py`

### Repositories (add user_id to constructor + queries)
- jobs/infrastructure/repositories/sa_job_repository.py
- companies/infrastructure/repositories/sa_company_repository.py
- companies/infrastructure/repositories/sa_company_intelligence_repository.py
- companies/infrastructure/repositories/sa_company_link_repository.py
- skills/infrastructure/repositories/sa_skill_repository.py
- skills/infrastructure/repositories/sa_skill_alias_repository.py
- skills/infrastructure/repositories/sa_skill_relationship_repository.py
- skills/infrastructure/repositories/sa_skill_link_repository.py
- skills/infrastructure/repositories/sa_skill_note_repository.py
- candidates/infrastructure/repositories/sa_candidate_repository.py
- candidates/infrastructure/repositories/sa_candidate_profile_repository.py
- candidates/infrastructure/repositories/sa_candidate_source_repository.py
- applications/infrastructure/repositories/sa_application_repository.py
- applications/infrastructure/repositories/sa_status_event_repository.py
- applications/infrastructure/repositories/sa_follow_up_repository.py
- applications/infrastructure/repositories/sa_note_repository.py
- applications/infrastructure/repositories/sa_document_repository.py
- roadmaps/infrastructure/repositories/sa_roadmap_repository.py
- placeholders/infrastructure/repositories/sa_placeholder_repository.py
- ai/infrastructure/repositories/llm_configuration_repository.py
- rules/infrastructure/repositories/sa_rule_repository.py
- cities/infrastructure/repositories/sa_city_repository.py

### DI + Routing
- `dependencies.py` — all factories gain user_id
- `shared/presentation/api/root_router.py` — inline routes gain auth

## Constraints

- No cross-context FKs (rule 15)
- Auth endpoints remain PUBLIC (no user_id required)
- Child tables (job_analysis, job_companies, etc.) inherit scope via parent
- Processing executions scope through their parent job
