# Code Reorganization Migration

## Migration Summary

This document tracks the reorganization from technical-layer-based structure to DDD bounded contexts.

## Phase 1: API Router Migration

**Moved**:
- `api/v1/jobs.py` → `jobs/presentation/api/jobs_router.py`
- `api/v1/skills.py` → `skills/presentation/api/skills_router.py`
- `api/v1/companies.py` → `companies/presentation/api/companies_router.py`
- `api/v1/insights.py` → `career/presentation/api/insights_router.py`
- `api/v1/pending.py` → `pending/presentation/api/pending_router.py`
- `api/v1/pending_companies.py` → `pending/presentation/api/pending_companies_router.py`
- `api/v1/resumes.py` → `resume/presentation/api/resumes_router.py`
- `api/v1/skill_roadmaps.py` → `skills/presentation/api/skill_roadmaps_router.py`
- `api/v1/rules.py` → `career/presentation/api/rules_router.py`
- `api/v1/dashboard.py` → `career/presentation/api/dashboard_router.py`
- `api/v1/websocket.py` → `shared/presentation/api/websocket_router.py`
- `api/v1/sse.py` → `shared/presentation/api/sse_router.py`

**Updated**: `api/router.py` to import from bounded contexts directly.

## Phase 2: Schema Migration

**Moved**:
- `schemas/jobs.py` → `jobs/presentation/api/schemas/jobs.py`
- `schemas/companies.py` → `companies/presentation/api/schemas/companies.py`
- `schemas/skills.py` → `skills/presentation/api/schemas/skills.py`
- `schemas/insights.py` → `career/presentation/api/schemas/insights.py`
- `schemas/pending.py` → `pending/presentation/api/schemas/pending.py`
- `schemas/resumes.py` → `resume/presentation/api/schemas/resumes.py`
- `schemas/rules.py` → `career/presentation/api/schemas/rules.py`
- `schemas/dashboard.py` → `career/presentation/api/schemas/dashboard.py`
- `schemas/skill_roadmaps.py` → `skills/presentation/api/schemas/skill_roadmaps.py`
- `schemas/common.py` → `shared/application/schemas/common.py`

## Phase 3: Services Migration

**Moved**:
- `services/worker.py` → `jobs/infrastructure/workers/worker.py`
- `services/company_worker.py` → `companies/infrastructure/workers/company_worker.py`
- `services/generation_worker.py` → `resume/infrastructure/workers/generation_worker.py`
- `services/insights.py` → `career/application/services/insights.py`
- `services/skill_roadmap_service.py` → `skills/application/services/skill_roadmap_service.py`
- `services/process_utils.py` → `shared/infrastructure/process_utils.py`
- `services/process/*` → `shared/infrastructure/process/*`

## Phase 4: Prompts Migration

**Moved**:
- `prompts/job_processing/*` → `jobs/infrastructure/ai/prompts/job_processing/`
- `prompts/company/*` → `companies/infrastructure/ai/prompts/company/`
- `prompts/resume/*` → `resume/infrastructure/ai/prompts/resume/`
- `prompts/skill_roadmaps/*` → `skills/infrastructure/ai/prompts/skill_roadmaps/`
- `prompts/insights/*` → `career/infrastructure/ai/prompts/insights/`
- `prompts/features_refactors/*` → `shared/infrastructure/ai/prompts/features_refactors/`

## Phase 5: Core Migration

**Moved**:
- `core/db.py` → `shared/infrastructure/config/db.py`
- `core/queue.py` → `shared/infrastructure/config/queue.py`

## Phase 6: Scripts Migration

**Moved**:
- `scripts/analyze_jobs.py` → `jobs/application/commands/analyze_jobs.py`
- `scripts/backfill_raw.py` → `jobs/application/commands/backfill_raw.py`
- `scripts/backfill_structured.py` → `jobs/application/commands/backfill_structured.py`
- `scripts/normalize_locations.py` → `jobs/application/commands/normalize_locations.py`
- `scripts/process_pending.py` → `jobs/application/commands/process_pending.py`
- `scripts/trigger_processor.py` → `shared/infrastructure/commands/trigger_processor.py`

## Phase 7: Root File Migration

**Moved**:
- `config.py` → `shared/infrastructure/config/app_config.py`
- `utils.py` → `shared/infrastructure/utils.py`
- `ai_compat.py` → `shared/infrastructure/ai/compat.py`
- `stream_server.py` → `shared/infrastructure/stream_server.py`
- `cli.py` → `shared/presentation/cli.py`

## Backward Compatibility

All original file locations contain re-export shims that import from the new locations.
This ensures existing code continues to work while imports are gradually updated.

## Import Update Strategy

1. **Immediate**: Update `main.py` and `api/router.py` to use new locations
2. **Gradual**: Update internal imports in moved files
3. **Legacy**: Keep re-export shims for external consumers
4. **Future**: Remove shims once all imports are updated
