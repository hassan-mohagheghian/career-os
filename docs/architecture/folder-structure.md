# Folder Structure

## Target DDD Structure

```
apps/backend/
├── entrypoints/                   # Application entry points
│   ├── cli.py                     # Typer CLI
│   └── api.py                     # FastAPI app + SocketIO
├── dependencies.py                  # FastAPI DI root
├── cli.py                           # CLI entry point (shared presentation)
├── exceptions.py                    # Backward-compatible re-exports
├── utils.py                         # Backward-compatible re-exports
│
├── jobs/                            # Jobs Bounded Context
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── job.py
│   │   │   └── summary.py
│   │   ├── value_objects/
│   │   │   ├── job_score.py
│   │   │   ├── job_location.py
│   │   │   └── workflow_log.py
│   │   └── repositories/
│   │       ├── job_repository.py
│   │       └── summary_repository.py
│   ├── application/
│   │   ├── use_cases/
│   │   │   └── list_jobs.py
│   │   ├── commands/
│   │   │   ├── analyze_jobs.py
│   │   │   ├── backfill_raw.py
│   │   │   ├── backfill_structured.py
│   │   │   ├── normalize_locations.py
│   │   │   └── process_pending.py
│   │   └── dto/
│   ├── infrastructure/
│   │   ├── models/
│   │   │   ├── job_model.py
│   │   │   └── misc_models.py
│   │   ├── repositories/
│   │   │   ├── sa_job_repository.py
│   │   │   └── sa_summary_repository.py
│   │   ├── workers/
│   │   │   └── worker.py
│   │   └── ai/prompts/job_processing/
│   │       ├── step2_validate.txt
│   │       ├── step3_extract_raw.txt
│   │       ├── step4_extract_struct.txt
│   │       └── step8_score.txt
│   └── presentation/
│       ├── api/
│       │   ├── jobs_router.py
│       │   └── schemas/jobs.py
│       └── cli/
│
├── companies/                       # Companies Bounded Context
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── company.py
│   │   │   ├── company_link.py
│   │   │   └── company_intelligence.py
│   │   └── repositories/
│   │       ├── company_repository.py
│   │       ├── company_link_repository.py
│   │       └── company_intelligence_repository.py
│   ├── application/
│   │   └── dto/
│   ├── infrastructure/
│   │   ├── models/
│   │   │   └── company_model.py
│   │   ├── repositories/
│   │   │   ├── sa_company_repository.py
│   │   │   ├── sa_company_link_repository.py
│   │   │   └── sa_company_intelligence_repository.py
│   │   └── ai/prompts/company/
│   │       ├── company_extract.txt
│   │       └── company_analyze.txt
│   └── presentation/
│       ├── api/
│       │   ├── companies_router.py
│       │   └── schemas/companies.py
│       └── cli/
│
├── skills/                          # Skills Bounded Context
│   ├── domain/
│   │   ├── entities/skill.py
│   │   └── repositories/
│   │       ├── skill_repository.py
│   │       ├── skill_alias_repository.py
│   │       └── skill_relationship_repository.py
│   ├── application/
│   │   ├── services/
│   │   └── dto/
│   ├── infrastructure/
│   │   ├── models/
│   │   │   └── skill_model.py
│   │   ├── repositories/
│   │   │   ├── sa_skill_repository.py
│   │   │   ├── sa_skill_alias_repository.py
│   │   │   └── sa_skill_relationship_repository.py
│   └── presentation/
│       ├── api/
│       │   ├── skills_router.py
│       │   └── schemas/
│       │       └── skills.py
│       └── cli/
│
├── rules/                           # Rules (Scoring) Bounded Context
│   ├── domain/
│   │   ├── entities/
│   │   │   └── rule.py
│   │   └── repositories/
│   │       └── rule_repository.py
│   ├── application/
│   │   └── dto/
│   ├── infrastructure/
│   │   ├── models/
│   │   └── repositories/
│   │       └── sa_rule_repository.py
│   └── presentation/
│       ├── api/
│       │   ├── rules_router.py
│       │   └── schemas/
│       │       └── rules.py
│       └── cli/
│
│                                        # Resume lives under jobs/ context:
│                                        #   jobs/domain/entities/resume.py
│                                        #   jobs/domain/repositories/resume_repository.py
│                                        #   jobs/infrastructure/repositories/sa_resume_repository.py
│                                        #   jobs/presentation/api/resumes_router.py
│                                        #   jobs/presentation/api/schemas/resumes.py
│
├── processing/                     # Processing Bounded Context (executions + queue)
│   ├── domain/
│   │   └── entities/processing_execution.py
│   ├── infrastructure/
│   └── presentation/api/
│       ├── executions_router.py    # prefix /processing
│       └── process_router.py       # prefix /jobs
│
├── shared/                          # Shared Kernel
│   ├── domain/
│   │   ├── entity.py
│   │   ├── value_object.py
│   │   ├── repository.py
│   │   └── domain_event.py
│   ├── application/
│   │   ├── dto.py
│   │   ├── exceptions.py
│   │   └── schemas/common.py
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── session.py
│   │   │   ├── sqlalchemy_config.py
│   │   │   ├── mappers.py
│   │   │   └── models/misc_models.py
│   │   ├── config/
│   │   │   ├── app_config.py
│   │   │   ├── db.py
│   │   │   └── queue.py
│   │   ├── process/
│   │   │   ├── process_manager.py
│   │   │   ├── temp_manager.py
│   │   │   ├── mimo_runner.py
│   │   │   ├── broadcaster.py
│   │   │   ├── repository.py
│   │   │   ├── logging_config.py
│   │   │   ├── worker_base.py
│   │   │   ├── models.py
│   │   │   └── interfaces.py
│   │   ├── websocket/
│   │   │   ├── manager.py
│   │   │   └── broadcaster.py
│   │   ├── workers/
│   │   │   └── background.py
│   │   ├── ai/
│   │   │   ├── compat.py
│   │   │   └── prompts/
│   │   ├── commands/
│   │   │   └── trigger_processor.py
│   │   ├── process_utils.py
│   │   └── utils.py
│   └── presentation/
│       ├── api/
│       │   ├── root_router.py      # Central API router (prefix="/api")
│       │   ├── websocket_router.py
│       │   └── sse_router.py
│       ├── cli.py
│       └── error_handler.py
│
├── core/                            # Legacy core (re-export shims)
│
├── schemas/                         # Legacy schemas (re-export shims)
│
├── services/                        # Legacy services (re-export shims)
│
├── scripts/                         # Legacy scripts (re-export shims)
│
└── prompts/                         # Legacy prompts (re-export shims)
```
