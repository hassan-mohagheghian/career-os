[33mcommit 15c3c69e773fe492d50df9c27d8d2cec1bb88b3a[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mmain[m[33m)[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 30 19:15:54 2026 +0330

    feat: add LLM Configurations feature with full CRUD and UI
    
    Backend (DDD layers in ai bounded context):
    - Domain entity, repository interface, and SQLAlchemy model
    - Repository implementation with get_all/get_enabled methods
    - REST API: list, get, create, update, delete, enable, disable
    - Pydantic schemas with validation
    - Alembic migration (shared_002) creating ai schema + llm_configurations table
    - Routes registered at /api/llm-configurations
    
    Frontend:
    - Entity types and typed API client with patch support
    - List page with loading/empty/error states and skeleton cards
    - Add/Edit/View drawers matching UX specs
    - Popover action menu (View, Edit, Enable/Disable, Delete)
    - Sidebar navigation: Settings > AI > LLM Configurations
    - Next.js page at /ai/llm-configurations
    
    Infrastructure:
    - Added 'ai' schema to SCHEMAS config
    - ensure_schemas() called during init_db to create schemas before tables

[33mcommit ab65528f310bab4e509411036a49ebd95894ec22[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 30 13:07:20 2026 +0330

    refactor: multi-schema alembic, storybook setup, and test alignment

[33mcommit ae33f304d15fe6904ba6c27388935dab663ff7bf[m[33m ([m[1;31morigin/main[m[33m)[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 20:49:34 2026 +0330

    fix: align tests with production code and improve system stability
    
    Backend:
    - Fix broadcaster room naming: use 'job_{pid}' for pending_jobs table
    - Migrate PendingJobRepository.count_by_status from ItemStatus to JobStatus
    - Update EXCLUDED_STATUSES from "completed" to "processed" in SA pending repo
    - Refactor ARQ client: remove global pool, use try/finally with per-call aclose
    - Add repair_llm_json utility for robust LLM response parsing
    - Update pending endpoint delete/reset/process to use correct status values
    - Fix stream_server to use repair_llm_json instead of raw json.loads
    - Add PYTHONPATH setup for background worker in start.py
    
    Frontend:
    - Update CardActions to remove non-existent Reset button
    - Add JobCreatedCard, JobProcessedCard, CompanyCreatedCard, CompanyProcessedCard
    - Add ScoresTab drawer component and url utility
    - Refactor pending/socket hooks and status config
    
    Tests (7 failing tests fixed):
    - test_broadcaster: assert job_42 room name matches production code
    - test_repository: use JobStatus enum and 'processed' status in count_by_status
    - test_sa_repositories: use 'processed' status for EXCLUDED_STATUSES tests
    - CardActions.test: remove Reset button assertions, fix processing status test

[33mcommit bd14e20b686b6da48040af957fd36ed9967f55b0[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 20:35:32 2026 +0330

    fix: WebSocket progress events and job worker table routing
    
    - Fix WorkflowProgress model: add table, pid, status, completed_nodes fields
    - Fix Broadcaster.progress(): use correct field names from WorkflowProgress
    - Fix _progress() in WorkerBase: pass table/status/completed_nodes
    - Fix JobWorker.table: return 'pending_jobs' instead of 'job' for correct room routing
    - Add progress emission in _update_node_status: emit pending:progress events
    - Add initial progress event when processing starts
    - Simplify JobStatus enum: consolidate to single 'processing' state
    - Fix _terminal_status and ACTIVE_STATUSES for new status model

[33mcommit f34521789e56d9df2ea2c75596d3708b9349cace[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 18:06:50 2026 +0330

    Add background worker (ARQ + Redis), reorganize docs, update README
    
    - Introduce app/background/ with ARQ worker infrastructure
    - Add Dockerfile.background and docker-compose.yml for worker deployment
    - Add queue infrastructure (arq_client.py, updated queue config)
    - Add background-related docs (background-service, workflows, arq, redis,
      deployment)
    - Add ADR-018 for background service architecture decision
    - Move app/server/ai/README.md → docs/ai/architecture.md
    - Move CLI.md → docs/development/cli.md
    - Update root README.md with accurate Next.js/FSD architecture, ARQ/Redis,
      background worker, current test counts, and corrected navigation
    - Add .next/ to .gitignore; untrack stale build artifacts
    - Update server routers for background queue integration
    - Update start.py with background command
    - Add CI workflow, update pyproject.toml and uv.lock
    - Add company processing pending router

[33mcommit 046e6988760cd0f0251aad8650889882731426cf[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 17:37:22 2026 +0330

    Migrate frontend to Next.js + FSD architecture
    
    - Set up Next.js App Router with FSD layers (app, entities,
      features, widgets, shared)
    - Replace Vite SPA with Next.js for all routes (/jobs, /companies,
      /resume, /rules, /skills)
    - Add TanStack Query for server state management
    - Fix shadcn UI components with proper React.forwardRef generics
    - Wire all page adapters to pass hooks props to legacy components
    - Add processing-status cards (Pending/Queued/Processing/Failed) to
      CompaniesPage left column
    - Move Add Company form above status cards to match JobsPage layout
    - Fix tailwind.config.js ESM compatibility (require → import)
    - Split test command into test {backend,frontend,all} subcommands
    - Add vitest + testing-library dependencies
    - Update tsconfig for Next.js, add next-env.d.ts, next.config.ts
    - Add docs for architecture decisions (ADR-016), FSD, TanStack Query,
      WebSocket integration

[33mcommit 750b8d3a8390c86eb61e9b1056d6bb0b61c13219[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 16:27:13 2026 +0330

    refactor: remove career and resume bounded contexts, consolidate into jobs context
    
    - Remove entire career/ and resume/ bounded contexts (domain, application, infrastructure, presentation)
    - Remove insights graph, prompts, and related frontend components
    - Remove old tests for removed modules
    - Move resume entities, repositories, and workers into jobs context
    - Add new alembic migrations for dropping unused tables
    - Add rules module and rename preferences to rules
    - Update all cross-references, imports, and DI wiring
    - Update docs to reflect the new structure

[33mcommit 848dc7c58662e6237421e7c9ee2a88ab11866bef[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 12:14:24 2026 +0330

    refactor: remove old processing module, consolidate lifecycle & pending handling
    
    - Delete deprecated app/server/processing module (models, repositories, routers)
    - Move alembic to app/alembic/ with fresh migration setup
    - Add domain events for jobs and companies (job/domain/events.py, company/domain/events.py)
    - Add shared domain lifecycle module (shared/domain/lifecycle.py)
    - Consolidate pending repositories into shared/infrastructure/database/
    - Move pending routers to companies/ and jobs/ presentation layers
    - Add new Typer-based app/start.py CLI
    - Update pyproject.toml with start script and pytest warning filters
    - Refactor client-side pages (CompaniesPage, JobsPage) to use simpler card components
    - Update tests to target new module locations and remove deprecated imports
    - Remove old root-level start.py

[33mcommit b733e75deaa6c8bc999c67fc04482810a6733f8c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 10:40:13 2026 +0330

    feat: add company processing graph with direct persistence and note/link fetching
    
    - Add load_context and DB persistence nodes to company LangGraph
    - Fetch and inline notes/links content during company processing
    - Add alembic migration 015 for company tracking columns
    - Refactor company worker to integrate with graph-based processing
    - Update frontend components for updated company status flow

[33mcommit 235e51ab27f8ee1305ecb08148dc6251f49fede6[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 10:04:50 2026 +0330

    Refactor card components into hierarchical status-based architecture
    
    - Add CardActions shared component with status-based button visibility
    - Add ProcessingCardFrame (root shared), StepProgress shared component
    - Add JobBaseCard, CompanyBaseCard as shared layer components
    - Create 5 job status cards: Pending, Queued, Processing, Failed, Completed
    - Create 5 company status cards: Pending, Queued, Processing, Failed, Completed
    - Integrate new cards into JobsPage and CompaniesPage
    - Add statusConfig shared constants
    - Fix PendingJobRepository missing update_fields method

[33mcommit 2947b5f906d52c71c685456e576d7d43420bdc62[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 29 09:30:15 2026 +0330

    refactor: overhaul job processing lifecycle with LangGraph state management
    
    - Refactor job/company graph processing with LangGraph runtime
    - Overhaul worker system with session-based streaming
    - Restructure stream server and WebSocket broadcasting
    - Extract Rust CLI tool (app/start/) in favor of start.py
    - Add alembic migrations for job lifecycle refactor
    - Update prompts, tests, and documentation

[33mcommit d6fa7d5767f7f354af1a1f547ad6218f31209c62[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 23:14:58 2026 +0330

    refactor: remove TEMP_DIR env var and file-based LLM result passing
    
    - Migrate all providers (opencode, mimo, agy) from file-based result
      files to stdout JSON parsing via generate_structured()
    - Remove TMP_DIR usage and temp file creation from:
      generation_worker, company_worker, backfill_structured,
      skill_roadmap_service, insights, AI graphs/tools, agy adapter
    - Update all prompt templates to emit JSON inline instead of
      writing to output_file
    - Hardcode TMP_DIR in mimo_runner/stream_server/backfill_raw
      (legacy workflows still use temp dirs internally but no longer
      depend on the env variable)
    - Delete TEMP_DIR from .env and all documentation references
    - Update tests to match new _run_mimo_prompt signature

[33mcommit 66f1b058f4c4c953fb84de346e735bbc5ee6c5c4[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 21:57:50 2026 +0330

    refactor(ai): migrate workflow state to LangGraph native management
    
    - Replace temp-file-based state passing with LangGraph State
    - Add checkpointing support (memory, sqlite, postgres backends)
    - Implement get_state/update_state on CompiledGraph
    - Add typed state classes (JobProcessingState, CompanyProcessingState, etc.)
    - Remove deprecated file I/O in tool layer (output_file, pid context)
    - Capture Write tool output from streaming events instead of reading result files
    - Fix TempFileManager singleton registry to actually track and clean up files
    - Remove docstrings and comments per project conventions

[33mcommit 5588a1adf372f0a71a02c4e40c8b148c0d58cb27[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 21:22:18 2026 +0330

    fix(tests): make generate-cover test platform-independent by using DI
    
    - Refactor generate_cover handler to accept session via FastAPI Depends
      instead of importing get_session_sync() inside the function body
    - Refactor generate_resume handler the same way for consistency
    - Remove monkey-patching (patch('dependencies.get_session_sync'))
      from test_generate_cover, test_generate_cover_not_found,
      test_generate_resume, and test_generate_resume_not_found
    - Use app.dependency_overrides for session injection instead
    - Add r.text to assertion messages for debuggability

[33mcommit fe98db4c0cc6d39602e9394e3cc55d0708957412[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 21:12:30 2026 +0330

    feat(ai): refactor tool layer, workers, and start script
    
    - Add unified Tool Layer (cache, fetch, web, models, registry modules)
    - Refactor job_tools, company_tools to use new Tool Layer
    - Update graph nodes (job, job_processing) to use new tools
    - Refactor company_worker, job worker, backfill_raw commands
    - Add stream server enhancements to root_router
    - Update test fixtures for opencode adapter and tool tests
    - Add Rust start script (version, config, process, ui, utils)

[33mcommit 90eae04c0386f86e49d36c1f771634a46e96c9c4[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 21:12:03 2026 +0330

    feat(ai): build Prompt Management Platform
    
    - Add PromptType enum, PromptSpec, PromptVersion base classes
    - Add PromptTemplate wrapping LangChain ChatPromptTemplate
    - Add 10 typed Pydantic input models per bounded context
    - Add PromptRegistry with semantic versioning support
    - Add 7 reusable prompt components (tone, formatting, JSON rules, etc.)
    - Add PromptLogger for observability
    - Implement 10 per-context prompts (jobs, companies, resume, skills, insights)
    - Add 56 tests covering rendering, versioning, edge cases, golden output
    - Add documentation: prompts.md, prompt-registry.md, prompt-versioning.md, prompt-testing.md
    - Add ADR-010: Prompt Management Platform
    - Backward compatible — legacy load_prompt() and PromptManager unchanged

[33mcommit f856d91e9e91f679e78153001dd2ffed59378fe5[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 21:04:58 2026 +0330

    feat(ai): add MockProvider for deterministic LLM testing
    
    Introduces a concrete LLMProvider implementation for tests that returns
    configurable canned responses, tracks call history, and supports error
    simulation via ProviderConfig.extra.
    
    - Create MockProvider in providers/mock/adapter.py
    - Register 'mock' in provider factory
    - Replace MagicMock(spec=LLMProvider) fixtures with real MockProvider
    - Rewrite test_service.py to use MockProvider with call tracking
    - Add 9 MockProvider tests plus factory registration test

[33mcommit f00b8302ae243e300a85e3918ba19e27896e5557[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:39:44 2026 +0330

    chore: remove deprecated GitLab CI config
    
    Remove .gitlab-ci.yml — project now uses GitHub Actions
    (.github/workflows/test.yml) for CI/CD.

[33mcommit 6271d7ee8845fe62001844129a039a9d27b03ef7[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:39:29 2026 +0330

    docs: update architecture, API, and testing documentation
    
    Update documentation across all architecture docs to reflect
    the new LangGraph-based AI workflow architecture:
    - ARCHITECTURE.md, backend-structure.md, folder-structure.md
    - modular-monolith.md, dependency-injection.md
    - api-design.md, backend-testing.md
    - Session docs for generation unification and history persistence
    
    Add new documentation:
    - docs/adr/006-rust-developer-cli.md
    - docs/architecture/developer-cli.md
    - docs/development/ directory
    - docs/prompts/ feature refactor prompts
    
    Update CI workflow, .gitignore, pyproject.toml, CLI.md, README.md.
    Update GenerationHistoryDrawer component for new workflow architecture.
    Add app/start/ module for application startup logic.

[33mcommit ba000361bb1604a8f01bc6ac7aad2e0590506e6b[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:38:57 2026 +0330

    test: restructure test suite into domain-organized directories
    
    Move tests from flat test_* files into domain-organized directories:
    - tests/ai/: AI agent, provider, service, tool, and workflow tests
    - tests/career/: Career insight unit tests
    - tests/companies/: Company intelligence tests
    - tests/jobs/: Job processing tests
    - tests/migration/: Response comparison migration tests
    - tests/processing/: Process manager, broadcaster, worker tests
    - tests/shared/: Shared infrastructure, repository, config, API tests
    - tests/skills/: Skill management tests
    - tests/utils/: Utility and schema tests
    
    Each directory follows the same structure as the source code:
    - infrastructure/: Repository and service tests
    - domain/: Model and value object tests
    - presentation/: API endpoint tests
    
    Updated conftest.py with shared fixtures for all test directories.

[33mcommit 2e987459d05f0124b541a8bd94b29a04426aaa69[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:38:30 2026 +0330

    feat(tools): enhance database, resume, and skill agent tools
    
    Expand database tools with comprehensive CRUD operations for all
    entity types: jobs, companies, skills, resumes, insights, preferences,
    and generation sessions.
    
    Update resume tools with improved tailoring logic and error handling.
    Update skill tools with category-aware operations and market analysis.
    
    Fix opencode adapter import path and clean up generation session
    repository interface.

[33mcommit c97b44120c4ecf77120909feba9608fbf09f4a3c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:38:01 2026 +0330

    feat(server): add entrypoints module for API and CLI
    
    Add app/server/entrypoints/ as the unified entry point module:
    - __init__.py: Module initialization
    - api.py: FastAPI application factory and route registration
    - cli.py: Typer CLI application for management commands
    
    Replaces the deleted app/server/cli.py and app/server/main.py
    with a cleaner separation of concerns.

[33mcommit 0836da927cc77e215b6a3c5c20f6a888075cecb4[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:37:37 2026 +0330

    feat(db): centralize SQLAlchemy models and add repository layer
    
    Add centralized database models under shared/infrastructure/database/models/:
    - CompanyModel, InsightModel, JobModel, PendingModel, SkillModel
    - Centralized schema definition for cross-bounded-context queries
    
    Add SQLAlchemy repository implementations (sa_*_repository.py):
    - Career insight, insight run, company intelligence, company link
    - Company, job, pending generation, pending, preference
    - Resume, skill alias, skill relationship, skill
    - Skill roadmap job, skill roadmap progress, skill roadmap
    - Summary, tech learning
    
    Update pending generation and pending repositories with improved
    query patterns and repository interfaces.
    
    Enhance AI compat layer and generation repository for consistency
    with new repository pattern.

[33mcommit d471e00e07b591ec911cf1866de55d0b7692b3ba[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:37:10 2026 +0330

    refactor: remove legacy CLI, startup scripts, and old test files
    
    Remove deprecated files that are no longer used:
    - app/server/cli.py, main.py, shared/presentation/cli.py (old Flask CLI)
    - app/server/static/api-docs/openapi.json (stale API docs)
    - start.sh (old startup script)
    - test_gemini_real.py (ad-hoc test script)
    - GEMINI.md, Modelfile, Modelfile1, TODO.md, app/README.md (obsolete docs)
    - tests/ (old root-level test directory, moved to app/server/tests/)
    - app/server/tests/test_*/ (old flat test files, restructured)
    
    Tests have been restructured into domain-organized directories
    under app/server/tests/ (career/, companies/, jobs/, etc.).

[33mcommit f3b62d72ce6b162162cefde169ecace5737f4616[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 20:34:40 2026 +0330

    feat(ai): migrate all generation workflows to LangGraph
    
    Migrate every AI generation workflow to independent LangGraph state
    machines with typed Pydantic outputs, retry support, and composable
    architecture.
    
    Runtime Infrastructure:
    - Add BaseState TypedDict as the unified state model for all graphs
    - Add 10 Pydantic output models for strongly typed graph outputs
    - Enhance GraphBuilder with per-node retry, checkpointing, streaming
    - Update AgentExecutor with structured logging and retry delay
    - Maintain backward compatibility with legacy GraphState wrapper
    
    Workflow Graphs (8 total):
    - job_processing: 12-node pipeline with retry on extract/score
    - company_processing: 7-node pipeline with retry on extract/analyze
    - resume_generation: 6-node pipeline for tailored resume creation
    - cover_letter_generation: 6-node pipeline for cover letters (new)
    - skill_extraction: 5-node pipeline for extracting skills from jobs (new)
    - skill_roadmap: 6-node pipeline for learning roadmap generation (new)
    - insights: 6 independent child graphs composed by parent orchestrator
    - generate_all: parent orchestrator coordinating all 7 workflow graphs
    
    Career Insights Child Graphs (each independently executable):
    - overview: career health score and summary
    - skills: skill gap analysis and recommendations
    - market: job market trends and analysis
    - companies: company intelligence and targeting
    - networking: professional network recommendations
    - opportunities: job opportunity funnel
    
    Prompts (per-graph ownership):
    - companies: extract_company.md, analyze_company.md
    - resume: tailor_resume.md, generate_cover_letter.md
    - skills: extract_skills.md, generate_roadmap.md
    - insights: overview.md
    
    Tests: 99 tests passing covering all graphs, models, retry paths
    Documentation: workflows.md, langgraph.md, graphs.md, insights.md, ADR
    
    Refs: 028__migrate_all_generation_workflows_to_langchan

[33mcommit 5dd52d02f88f4c7fcace61b06e0aca34c0925ee8[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 17:18:06 2026 +0330

    refactor: restructure AI as DDD bounded context under server/ai
    
    - Move all AI code from app/ai/ to app/server/ai/ bounded context
    - Add DDD layers: domain, application, infrastructure, presentation
    - Create domain entities: GenerationSession
    - Create domain value objects: GraphState, ProviderConfig, ProviderResponse
    - Create domain repositories: IGenerationSessionRepository
    - Create application layer: ProcessJobUseCase, commands, DTOs
    - Create infrastructure: providers, graphs, tools, prompts, parsers
    - Add 12-stage Job Processing Graph with LangGraph support
    - Add progress reporting system with WebSocket events
    - Add structured output parsing with Pydantic models
    - Add error handling strategies: retry, fallback, graceful degradation
    - Add prompt management system per graph node
    - Add reusable LangChain tools for job processing
    - Remove old app/ai/ directory
    - Update imports and dependencies

[33mcommit e91845523e3109f5414da5420eb1fa9d492f80ac[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 15:01:34 2026 +0330

    fix: company reprocess pipeline and graceful URL error handling
    
    - Reprocess endpoint now passes company_id and existing links to pending record
    - _save_company uses pending item's company_id to UPDATE instead of INSERT
    - create_pending_company accepts optional company_id and links params
    - Fetch step filters out failed URLs from LLM content (only valid content sent)
    - Pipeline continues with notes-only if all links fail (links are optional)
    - Failed URLs are logged but not included in raw_content sent to extraction

[33mcommit d909c043a058b5093c72cc5bb7774bceec1b79c9[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 10:24:19 2026 +0330

    refactor: modular monolith DDD bounded contexts with test fixes
    
    - Restructure into bounded contexts: career, companies, jobs, pending, resume, shared, skills
    - Move domain entities, repositories, and infrastructure into context-specific modules
    - Fix lazy import path for SQLAlchemySkillRoadmapProgressRepository (__init__.py)
    - Fix sa_session test fixture to handle rollback state errors gracefully
    - Add httpx2 dependency groups for test compatibility
    - Remove old domain/ and infrastructure/ flat module structure
    - Remove prompts/features_refactors/ directory
    - Add architecture docs (ADR, DDD structure, hexagonal architecture)
    - Update all v1 API routers and dependencies for new module paths

[33mcommit ba7e7d62a342fea825ba903d641334167a28cfa6[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 28 08:32:04 2026 +0330

    test: add comprehensive test suite, configure coverage, and fix minor issues
    
    - Add Vitest coverage-v8 with 92% threshold targets
    - Add unit tests for all client features (companies, insights, jobs, resume, rules, skills)
    - Add unit tests for shared components, layout, and utility functions
    - Add server-side tests for API endpoints, services, and utilities
    - Add 'Nice to Have' section to StructuredTab component
    - Fix pending_repo.create() signature (remove redundant url parameter)
    - Remove unnecessary try/finally blocks in generation endpoints

[33mcommit 8040a15e1ba0f7cc71865ab0ab600af5a15b1f81[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Mon Jul 27 21:06:58 2026 +0330

    refactor: eliminate ALL raw SQL from tests, scripts, and process repository
    
    - Rewrite services/process/repository.py: replace sqlite3 with SA sessions
      (PendingJobRepository, PendingCompanyRepository, JobRepository)
    - Rewrite tests/conftest.py: replace ALL_TABLES CREATE TABLE with Base.metadata.create_all
    - Rewrite 8 test files to use SA ORM instead of sqlite3:
      - test_process/test_repository.py
      - test_services/test_worker_services.py
      - test_services/test_generation_repository.py
      - test_services/test_insights_unit.py
      - test_services/test_worker_broadcast.py
      - test_services/test_company_worker.py
      - test_process/test_skill_management.py
      - test_core/test_queue.py
    - Rewrite 5 scripts to use SA (analyze_jobs, backfill_raw, backfill_structured,
      normalize_locations, process_pending)
    - Update 11 docs to reflect SQLAlchemy+Alembic architecture (no raw SQL)
    - Zero sqlite3 references remain in codebase (confirmed by grep audit)
    - All 256 tests pass

[33mcommit dd8dec476ab2ee4be4d69bc98730dcf3959fa90c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Mon Jul 27 20:33:37 2026 +0330

    refactor: eliminate all raw SQL, complete SQLAlchemy ORM migration
    
    - Delete migrations.py, database.py, and 5 legacy raw-SQL repositories
      (job_repository, company_repository, skill_repository, pending_repository,
      insight_repository)
    - Add 14 new domain interfaces + 14 SA repository implementations for all
      remaining tables (career_insights, company_intelligence, company_links,
      pending_generations, preferences, resumes, summaries, tech_learning,
      skill_aliases, skill_relationships, skill_roadmaps, skill_roadmap_progress,
      skill_roadmap_jobs)
    - Rewire all 12 API route files to use SA repos via Depends(get_*_repo)
    - Rewrite dependencies.py with SA-only DI (19 repo providers, no sqlite3)
    - Refactor all services with raw SQL: worker, company_worker, generation_worker
      (both files), skill_roadmap_service, queue, insights, stream_server
    - Refactor cli.py to use SA repos (no get_db)
    - Rewrite core/db.py to use Base.metadata.create_all() + seed data
    - Fix main.py lifespan (replace deleted migrations import with init_db)
    - Add SPA catch-all route for serving frontend dist/index.html
    - Fix skills.created_at, jobs.updated_at/title/description missing DB columns
    - Fix 256 tests (0 failures) with SA mocking and ORM-based test fixtures
    - All endpoints verified: 15 API routes + 6 frontend routes return 200

[33mcommit 6eb089d5946e938d1d7182183cdbdb591f7b8790[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Mon Jul 27 18:29:07 2026 +0330

    feat: add SQLAlchemy ORM layer and Alembic migrations
    
    - Add SQLAlchemy 2.x ORM models for all 20+ tables
    - Add Alembic with initial baseline migration
    - Add domain-to-DB mapping layer (dict ↔ ORM)
    - Add SA repository implementations (job, skill, company, pending, insight)
    - Integrate Alembic into startup and start.sh
    - Add SA session dependencies and DI wiring
    - Add SA test fixtures and architecture docs
    - Keep legacy sqlite3 repositories for backward compatibility

[33mcommit 4e3260fe9701b9d107e5e50246db324a7c9c22ba[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Mon Jul 27 17:50:11 2026 +0330

    feat: refactor generation pipeline, overhaul insights UI, and add deep linking
    
    - Add unified generation models and repository for resume/cover history
    - Extract generation_worker, company_worker, insights_service, skill_roadmap_service
      into dedicated process modules
    - Consolidate SkillRoadmapDrawer into SkillDetailDrawer
    - Add per-job generation history endpoint and inline generation triggers
    - Enhance job detail endpoint with embedded resume/cover data
    - Add deep linking for companies, skills, and insights sub-tabs
    - Add generation history drawer with local history persistence
    - Add collapsible UI component and time formatting utilities
    - Update frontend to use activeGens instead of generationProgress
    - Add opencode AI provider
    - Update architecture docs, changelog, and feature list
    - Add tests for generation models, repository, and worker services

[33mcommit c5af9b09018a151988c01917e275ba9995c61b7f[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Mon Jul 27 08:08:47 2026 +0330

    refactor: flask to fastapi

[33mcommit 2c76ecc051b8a08a930b7bbc043df95c3c68902e[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 26 01:15:44 2026 +0330

    docs: comprehensive documentation update for AI agent layer
    
    Update all 13 documentation files to reflect current project state:
    
    - ARCHITECTURE.md: Updated system diagram, backend structure, data flows
    - CONTEXT.md: Updated rules, system boundaries, Python 3.14
    - DEVELOPMENT.md: Updated env vars, testing, code style
    - CHANGELOG.md: Added v2.2.0 and v2.1.0 entries
    - DOMAIN.md: Updated processing pipelines, generation workflow
    - FEATURES.md: Added AI Agent Orchestration feature section
    - README.md: Updated architecture overview, documentation index
    - ADR-004: New ADR for AI Agent Orchestration Layer
    - PROJECT_CONTEXT.md: Updated tech stack, AI architecture
    - AI_AGENTS.md: Updated imports, patterns, test count
    - AI_ARCHITECTURE.md: Added service.py, test_service.py
    
    All tests pass (376 total).

[33mcommit 908e0675a0b8150c76285700dc3f7c0395731d35[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 26 01:08:44 2026 +0330

    feat: WebSocket progress for resume/cover generation + immediate display + session_id
    
    Replace polling with WebSocket real-time updates for resume/cover
    generation, matching the pattern used by jobs, companies, and insights.
    
    Backend:
    - Generation worker emits WebSocket events via broadcaster
    - broadcaster handles pending_generations table (generation: prefix)
    - SocketIO watch/unwatch handlers for generation rooms
    - Generation history shows session_id from pending_generations
    
    Frontend:
    - useResume hook listens for generation:update/complete/error events
    - watchGeneration/unwatchGeneration for room management
    - Drawer updates immediately on generation:complete event
    - No more polling — pure WebSocket real-time updates
    - generationResult state for immediate content display
    
    All 306 tests pass, frontend builds successfully.

[33mcommit 74c9ba2013e3f7e76a7d5804766e90896aba5d40[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 26 00:56:43 2026 +0330

    fix: escape curly braces in company context for prompt template
    
    The company_context_str contains JSON data with curly braces (e.g.,
    {"overview": ...}). When passed to load_prompt() which uses
    template.format(**kwargs), the braces break the template rendering,
    causing mimo to never write the result file.
    
    Fixed by escaping { and } in company_context_str before passing to
    load_prompt, so template.format() treats them as literal characters.

[33mcommit 787727350e5f911cc5751dfe2a7fb6bb329921a1[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 26 00:47:14 2026 +0330

    fix: remove double type prefix in generation worker pid
    
    The prompt templates already add 'cover_' or 'resume_' prefix to the
    pid (e.g., cover_{pid}.json), but the pid variable also included the
    gen_type prefix, resulting in cover_cover_257_xxx.json.
    
    Changed pid from 'cover_257_1785014148590' to '257_1785014148590'
    so the final path becomes 'cover_257_1785014148590.json'.

[33mcommit b66a116daa8890a2a1a1355f87917304eba62e69[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 26 00:44:27 2026 +0330

    fix: sqlite3.Row .get() error in generation worker
    
    The rule_rows query returns sqlite3.Row objects which don't have a
    .get() method. Convert each row to dict before calling .get().
    
    Fixed line 188: r.get('score_weight') -> dict(r).get('score_weight')

[33mcommit c0736aefcc581234db37c5fb6e68b380d4edea4f[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 26 00:38:48 2026 +0330

    fix: resume/cover generation progress bars and generation history
    
    Fix three issues with the new async resume/cover generation:
    
    1. sqlite3.Row .get() error: _load_company_context was receiving a
       closed connection. Fixed by having it open its own connection.
    
    2. Progress bars not showing: useResume hook wasn't including the
       'type' field (resume/cover) in the generationProgress object.
       Added generationType state and passed it to progress polling.
    
    3. Generation history missing: Added pending_generations query to the
       /api/generation-history endpoint so resume/cover generations appear
       in the unified history list.
    
    All 306 tests pass, frontend builds successfully.

[33mcommit 485c4cac7a8a8700369501edb84d73abe26e5633[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 26 00:12:52 2026 +0330

    feat: async resume/cover generation with progress bars and company context
    
    Add background processing for resume and cover letter generation with
    step-by-step progress tracking, matching the pattern used by jobs,
    companies, and skills intelligence.
    
    Backend:
    - New pending_generations table for tracking generation progress
    - Background worker (generation_worker.py) with 5-step pipeline
    - Async API endpoints: POST /api/jobs/:num/generate-resume/cover
    - Progress polling: GET /api/generations/:id
    - Cancel support: POST /api/generations/:id/cancel
    - Company intelligence enrichment: loads linked company data into prompt
    - Updated prompts to accept company_context parameter
    
    Frontend:
    - DocumentsTab now shows GenerationProgressCard with step progress
    - useResume hook tracks progress via polling (2s interval)
    - Cancel button during generation
    - Automatic refresh on completion
    - Error display with retry
    
    Company Context:
    - When job is linked to a company, loads company intelligence
    - Enriches resume/cover prompts with tech stack, culture, visa info
    - Helps generate more targeted, company-specific documents
    
    All 376 tests pass, frontend builds successfully.

[33mcommit 8ff8f418bb4019e9ef5e2dc204ea02986bc722e0[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 23:01:44 2026 +0330

    feat: migrate all AI calls to LLMService provider abstraction
    
    Replace all 15 direct MimoRunner/subprocess calls across 7 files
    with the unified LLMService entry point. The AI agent layer is now
    the single source of truth for all LLM interactions.
    
    New:
    - app/ai/service.py: LLMService with generate/generate_structured/
      generate_streaming methods
    - app/server/ai_compat.py: server-compatible import helper
    - tests/test_ai/test_service.py: 11 tests for LLMService
    
    Migrated files:
    - services/worker.py: 6 call sites (extract, validate, score, stream)
    - services/company_worker.py: 2 call sites (extract, analyze)
    - services/insights.py: 1 call site (all career intelligence)
    - blueprints/resumes.py: 2 call sites (resume, cover generation)
    - blueprints/skill_roadmaps.py: 2 call sites (generate, extend)
    - stream_server.py: 1 call site (async streaming)
    - scripts/backfill_structured.py: 1 call site (backfill)
    
    Enhanced:
    - MimoProvider: added generate_streaming() with on_event/on_session_id
    - Updated tests to mock LLMService instead of MimoRunner
    - AI_ARCHITECTURE.md: added LLMService documentation
    
    All 376 tests pass (70 AI + 306 server).

[33mcommit 344863f9ef68e3275c0a1103e54bab53af603690[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 18:45:54 2026 +0330

    feat: introduce AI Agent Orchestration Layer with multi-provider support
    
    Add a production-grade agent system wrapping the existing Mimo CLI
    integration with a provider abstraction, LangGraph workflow engine,
    and tool-based architecture.
    
    Provider Layer:
    - LLMProvider ABC with generate() and generate_structured()
    - MimoProvider wrapping existing MimoRunner subprocess logic
    - OpenAIProvider and LocalLLMProvider stubs for future providers
    - Factory with dynamic selection via AI_PROVIDER env var
    
    Agent Runtime:
    - AgentState value object for graph state management
    - AgentExecutor with retry logic and structured logging
    - AgentRegistry singleton for agent discovery
    - GraphBuilder with LangGraph StateGraph compilation
    
    6 Agent Implementations:
    - JobExtractorAgent, JobAnalyzerAgent, JobScorerAgent
    - CompanyResearcherAgent, CompanyEvaluatorAgent
    - SkillIntelligenceAgent, ResumeAgent, InsightsAgent
    
    3 Workflow Graphs:
    - JobProcessingGraph: fetch -> validate -> extract -> score
    - CompanyProcessingGraph: fetch -> extract -> analyze -> save
    - InsightsGenerationGraph: overview -> opportunities -> ... -> skills_intel
    
    Tool System (10 tools):
    - Wraps existing services (worker.py, company_worker.py)
    - BaseTool ABC with ToolResult value object
    - Job, company, skill, resume, and database tools
    
    Infrastructure:
    - Upgraded Python to 3.14 (stable) for langgraph compatibility
    - Updated GitHub Actions to Python 3.14
    - start.sh uses venv python, shows AI provider config
    - AI_ARCHITECTURE.md full documentation
    - 59 tests passing (TDD approach)
    
    Design principles: DDD, SOLID, TDD, Factory/Strategy/Registry/
    Builder/Observer/Command patterns throughout.

[33mcommit 9362483a1874a429e664d357d484bbc2a631f424[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 18:08:48 2026 +0330

    fix: replace window.confirm with ConfirmDialog component
    
    All 3 confirmation dialogs in SkillsIntelSection (hide skill, delete
    skill, merge skills) now use the app's ConfirmDialog component instead
    of the browser's native window.confirm, providing consistent UX.

[33mcommit 0a17c9c777bd32ea17e99e8c298b1900296b3b0f[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 18:04:48 2026 +0330

    refactor: rename tech_stack → skills across full stack
    
    Rename the tech_stack table, blueprint, API routes, and all references
    to "skills" for accurate naming since the system handles all skill types
    (technical, engineering, professional, domain, career) — not just tech.
    
    Database:
    - Rename table tech_stack → skills via migration
    - Update schema definition and FK references
    
    Backend:
    - Rename blueprint tech_stack.py → skills.py
    - Rename all API routes /api/tech-stack → /api/skills
    - Update all SQL queries across services and blueprints
    - Fix migration ordering (pre-rename migrations use old table name)
    
    Frontend:
    - Update all fetch calls from /api/tech-stack to /api/skills
    
    Tests:
    - Update all test fixtures and SQL to use skills table
    - All 290 tests pass

[33mcommit 76573a0fb3e9f3e3b5fed1fefe246f59e55f704d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 17:44:26 2026 +0330

    fix: allow PUT /api/tech-stack to update all skill fields
    
    Add category, confidence, market_relevance, evidence, and source_type
    to the allowed update fields so skills of all types (technical,
    engineering, professional, domain, career) can be fully managed.

[33mcommit e94ffdf7ad44e7c601ba5e30529618c82a65b531[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 17:43:00 2026 +0330

    feat: Skills Intelligence dashboard with full skill management center
    
    Replace the Insights → Skills placeholder with a comprehensive intelligence
    dashboard featuring career readiness gauge, market demand charts, skill gap
    matrix, AI recommendations, and learning roadmap preview. Enhance the root
    Skills tab with intelligence summary and auto-refresh.
    
    Backend:
    - Add /api/skills-intelligence/dashboard aggregation endpoint
    - Add /api/tech-stack/categories, /stats, /bulk-hide, /bulk-categorize
    - Fix POST /api/tech-stack to persist category and source_type
    - Enhance skill normalization with alias resolution and deduplication
    - Extend skills_intelligence prompt with dashboard-ready output fields
    
    Frontend:
    - New SkillsIntelDashboard component with recharts bar chart
    - SkillsTab intelligence summary header with refresh and navigation
    - SkillDetailDrawer job market evidence section
    - Deep linking support for #insights/skills hash

[33mcommit 7dc905bb8f3204f31d7b32612b7bdc1c2ee65a0f[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 16:49:55 2026 +0330

    docs: Skills Intelligence redesign plan + PROJECT_CONTEXT.md
    
    Phase 0: Created PROJECT_CONTEXT.md — complete project brain document
    Phase 1-10: Created skills_intelligence_redesign.md with full implementation plan
    
    Key findings:
    - AI insights stored as JSON blob, never propagated to tech_stack DB
    - skill_evidence table needed for tracking skill sources
    - Market skill extraction agent needed
    - Skills Intelligence page needs: Overview Cards, Market Demand Chart, Gap Matrix, Recommendations, Roadmap Preview
    - _fill_skills_from_insights() needs enhancement to propagate ALL AI data to DB
    
    Implementation plan covers:
    - Database: skill_evidence table, tech_stack columns
    - Backend: evidence endpoints, enhanced _fill_skills_from_insights()
    - AI Pipeline: updated skills_intelligence.txt, new skills_market_analysis.txt
    - Frontend: SkillsIntelligencePage, MarketDemandChart, SkillGapMatrix, RecommendationCard, RoadmapPreview

[33mcommit a13ff9a6ebb68c6e500203942a1d23433981dbb2[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 16:36:26 2026 +0330

    docs: complete documentation structure per 015_docs.txt
    
    New files:
    - CONTEXT.md — Project memory for AI agents and humans
    - DOMAIN.md — Entities, business rules, workflows
    - FEATURES.md — Product capabilities with goals/status
    - API.md — All endpoints with request/response examples
    - DEVELOPMENT.md — Setup, testing, code style, git workflow
    - AI_AGENTS.md — Agent instructions, coding rules, change guidelines
    - DECISIONS/ADR-001-architecture-style.md
    - DECISIONS/ADR-002-database-choice.md
    - DECISIONS/ADR-003-ai-integration.md
    - RUNBOOKS/deployment.md
    - RUNBOOKS/troubleshooting.md
    
    Updated:
    - CHANGELOG.md — Added v2.0.0 entry with all recent changes
    - docs/README.md — Documentation index with audience guidance
    - docs/architecture/ARCHITECTURE.md — Complete system reference

[33mcommit 9c0cedd512eaffde69e0d259802c7d436c453657[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 15:41:43 2026 +0330

    docs: comprehensive documentation update for humans and AI agents
    
    Root README.md:
    - Updated navigation structure (Skills top-level, Growth Path removed)
    - Added complete API endpoints table
    - Updated project structure with current feature-based architecture
    - Updated tech stack (TypeScript, 306+23 tests)
    - Added API docs section
    
    docs/README.md:
    - Rewritten as documentation index
    - Added audience-specific guidance (AI agents, developers, PMs)
    - Listed all doc files with purposes
    
    docs/architecture/ARCHITECTURE.md:
    - Complete system overview with ASCII diagram
    - Full entity list with table names
    - Navigation structure diagram
    - Backend structure with all 10 blueprints
    - Data flow diagrams for all processes
    - Complete API endpoints reference
    - WebSocket events table
    - Design decisions documented
    
    Cleanup:
    - Removed stale docs: career_intelligence.md, PROJECT_CONTEXT.md, ROADMAP.md, worker-architecture.md
    - Removed stale docs/agent/ directory (done in previous commit)

[33mcommit 5bc5256180638bf21865bc1fffbfd859ec9e8759[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 15:29:14 2026 +0330

    refactor: reorganize navigation, clean up header, simplify sidebar
    
    Navigation:
    - Skills is now a top-level menu between Companies and Insights
    - Insights → Skills sub-tab is an empty placeholder (new design pending)
    - Growth Path section removed (Skills moved to top-level)
    - Insights menu fixed (always expanded, no collapse toggle)
    - Settings section: Resume + Rules
    
    Header:
    - Removed stat badges (jobs/match/apply/remote/companies/resumes)
    - Theme toggle and History button moved to right side
    - Removed unused imports (Target, Rocket, House, StatBadge)
    
    Sidebar:
    - Removed expand/collapse toggle for Insights (always shows children)
    - Cleaned up unused state and functions
    
    Skills:
    - Growth Path → Skills: full skill management (categories, filters, merge, CRUD, roadmaps)
    - Insights → Skills: empty placeholder for future design
    - _fill_skills_from_insights() fills AI-generated skills into tech_stack DB
    
    Tests: 306 backend + 23 frontend all pass

[33mcommit 92fc7a744c476987f892f0193fc0c6927471417d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 14:32:24 2026 +0330

    feat: unified job/company adding with NotesLinksInput shared component
    
    - Created shared NotesLinksInput component (notes textarea + links with title tags)
    - Updated JobsPage to use NotesLinksInput instead of URL-only input
    - Updated usePending.ts to accept optional notes/links in submitUrl()
    - Backend already supports notes/links (from previous commit)
    - Both jobs and companies now have consistent adding UX

[33mcommit 75e0fde51025ab91d4ea8bcbdf93e320c4fbc5ce[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 14:29:38 2026 +0330

    fix: move Skills under Insights, remove Growth Hub section
    
    - Skills is now a sub-tab inside Insights (alongside Overview, Opportunities, etc.)
    - Removed standalone Skills tab from App.tsx
    - Added Skills to InsightsTab TabsTrigger and render block
    - Removed 'growth hub' from Sidebar section list (empty now)
    - Sidebar now: JOBS (Jobs, Companies, Insights→6 sub-tabs), SETTINGS (Resume, Rules)

[33mcommit e912ee79880de7b3b5c932a928677c9ad4dbc8a4[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 14:16:24 2026 +0330

    feat: add notes+links support to job processing pipeline
    
    Backend:
    - Added notes/links columns to pending_jobs (DB schema + migration)
    - Updated POST /api/pending to accept {notes, links, url} for multi-source input
    - Added _fetch_multi_source() in worker.py to iterate over notes+links
    - Updated process_job() to use notes/links when available, falls back to URL-only
    - Updated all test fixtures with new columns
    
    This enables users to add jobs with notes and links (like companies),
    while keeping the job-specific processing pipeline (fetch→validate→extract→score→save).

[33mcommit 85fcf3f35705134b4996b3ca25109bd2cb8b5c61[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 14:06:04 2026 +0330

    fix: mock HTTP calls in fetch URL tests instead of hitting real httpbin.org
    
    - test_fetch_404_raises: mock urllib.request.urlopen with HTTPError(404)
    - test_fetch_403_raises: mock urllib.request.urlopen with HTTPError(403)
    - Eliminates flaky test failures from external service timeouts
    - All 306 backend tests pass

[33mcommit cb99b7185c75fc1e29fe1db4aef99e03d9f0ca7a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 13:59:58 2026 +0330

    fix: remove redundant Insights section header, move Insights under Jobs
    
    - Insights moved from 'insights' section to 'jobs' section (alongside Jobs/Companies)
    - Removed 'insights' from Sidebar section list
    - Sidebar now: JOBS (Jobs, Companies, Insights), GROWTH HUB (Skills), SETTINGS (Resume, Rules)

[33mcommit adc8a6d49a4076e7d9cbd5447147b8ef90f8219c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 13:54:58 2026 +0330

    refactor: reorganize navigation — Insights root, Growth Hub→Skills, Settings
    
    New structure:
      Jobs (section: jobs)
      Companies (section: jobs)
      Insights (section: insights) → Overview, Opportunities, Companies, Market, Networking
      Growth Hub (section: growth hub) → Skills
      Settings (section: settings) → Resume, Rules
    
    Changes:
    - App.tsx: moved Insights to own section, Skills to Growth Hub, Resume/Rules to Settings
    - Sidebar.tsx: added 'insights' to section list
    - InsightsTab.tsx: removed Skills sub-tab and SkillsIntelSection
    - SkillsTab.tsx: wired into App.tsx render (was already built but disconnected)

[33mcommit eff98a69241af5fec123aee73f94647827b34742[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 13:37:46 2026 +0330

    feat: move Skills into Insights sub-tab + rename 'analysis' to 'Growth Hub'
    
    - Skills is now a sub-tab inside Insights (not a top-level tab)
    - Sidebar section renamed from 'analysis' to 'Growth Hub'
    - Removed SkillsTab from App.tsx render (now rendered inside InsightsTab)
    - Added Skills sub-tab to InsightsTab TabsTrigger list
    - Added SkillsIntelSection render block in InsightsTab
    - Removed Skills from Header FEATURES array
    - Removed redirect guard for skills in InsightsTab
    - Fixed 'Insightsligence' typo in InsightsTab title
    - Backend: fixed double-prefixed career_career_insight_runs table refs

[33mcommit c4ff8cb497dffb4e0375784b60e4718c7488135f[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 13:20:02 2026 +0330

    docs: update all documentation to reflect current codebase
    
    - Rewrote README.md with current tech stack (TypeScript, 267+23 tests, API docs)
    - Rewrote ARCHITECTURE.md with feature-based frontend, renamed Insights
    - Updated CHANGELOG.md with all recent changes
    - Removed stale agent docs (docs/agent/)
    - Updated project structure to show features/, shared/, layout/
    - Updated API endpoints to reflect renamed routes
    - Updated WebSocket events to use new naming
    - Added API docs section (Swagger UI + ReDoc)

[33mcommit 354b7520c69d5ea6c97c0fa4ae9dd399c7ddb111[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 13:14:18 2026 +0330

    refactor: rename career-intel to insights everywhere
    
    Backend:
    - services/career_intel.py → services/insights.py
    - blueprints/career_intel.py → blueprints/insights.py
    - prompts/career_intel/ → prompts/insights/
    - SocketIO events: career_intel:progress → insights:progress, watch/unwatch career_intel → insights
    - Blueprint name: career_intel → insights
    - All imports, log prefixes, docstrings updated
    
    Frontend:
    - features/career-intel/ → features/insights/
    - CareerIntelTab.tsx → InsightsTab.tsx
    - useCareerIntel.ts → useInsights.ts
    - Tab ID: career-intel → insights
    - Hash routing: #career-intel/overview → #insights/overview
    - All imports and references updated
    - GenerationHistoryDrawer source: career-intel → insights
    
    Tests:
    - test_career_intel_unit.py → test_insights_unit.py
    - test_career_intel_streaming.py → test_insights_streaming.py
    - All test references updated

[33mcommit 2db4642492f3d17022926de164d1a1d323498e0a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 13:01:05 2026 +0330

    feat: add live API documentation (Swagger UI + ReDoc)
    
    - Created static OpenAPI 3.0 spec with 24 endpoints documented
    - Created api_docs blueprint serving Swagger UI at /api/docs/
    - Created ReDoc viewer at /api/redoc/
    - Added Swagger docstrings to key routes (jobs, skills, insights)
    - API spec covers: Jobs, Companies, Skills, Insights, Queue, Rules, Resumes, System
    - No external dependencies — uses CDN for Swagger UI and ReDoc
    - All 267 backend + 23 frontend tests pass

[33mcommit 31fc48d61cda2bef9abc21b31962c03ce7fd84df[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 12:46:03 2026 +0330

    fix: hide duplicate progress bars during skills generation
    
    - SkillsTab now passes empty genJobs array when main skills_intel generation is running
    - Prevents SkillsIntelSection from rendering individual genJob cards on top of the main progress card
    - Fixes 4x 'Generating... 0/4' progress bars appearing simultaneously

[33mcommit fcfbe364e0e1637586d3bca78539de8ae6352ea5[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 12:38:43 2026 +0330

    feat: extract Skills into independent top-level tab
    
    - Created useSkills hook: extracts skills state from App.tsx (skillRoadmapProgress, skillGenJobs, SocketIO listener, refresh/cancel)
    - Created SkillsTab component: standalone page wrapping SkillsIntelSection with own header, refresh, progress card
    - Updated CareerIntelTab: removed Skills sub-tab, SkillsIntelSection import, skills-related props
    - Updated App.tsx: added Skills as top-level tab (between Companies and Resume), removed all skills state/props/socketio
    - Updated Header.tsx: added Skills to FEATURES array with rose color
    - Updated test: generate_all() now tests 5 sections (skills excluded as independent)
    - No backend changes needed — generate_all() already excluded skills_intel

[33mcommit a3e4c4c27e92af193ec0ab69ae2a18c4f9c3420e[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 11:54:43 2026 +0330

    refactor: cleanup unused files + consistent font size system
    
    Cleanup:
    - Removed empty directories (components/profile, hooks, lib, shared/types, feature api/types dirs)
    - Restored accidentally deleted RulesTab.tsx
    
    Font size system:
    - Added text-3xs (6px) and text-2xs (8px) to Tailwind theme
    - Replaced all 353 arbitrary text-[0.XXrem] values with semantic tokens
    - Single source of truth: tailwind.config.js fontSize extension
    - Scale: 3xs→2xs→xs→sm→base→lg→xl→2xl→3xl→4xl→5xl
    - No more arbitrary font sizes in the codebase

[33mcommit e59f9e4e9b823e0790cfac604a565eea8e1f4823[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 11:46:22 2026 +0330

    refactor: restructure frontend to feature-based architecture
    
    New structure:
      features/
        jobs/          (components, hooks, tests)
        companies/     (components, hooks)
        career-intel/  (components, hooks)
        resume/        (components, hooks)
        rules/         (components)
      shared/
        ui/            (shadcn components)
        components/    (ConfirmDialog, ProcessingItem, GenerationProgressCard, etc.)
        hooks/         (useSocketIO, usePending, useWorkflow, useToast + index re-exports)
        lib/           (utils, skills + index re-exports)
      layout/          (Header, Sidebar)
      App.tsx, main.tsx
    
    All imports updated to new paths. Build passes, 23 frontend + 267 backend tests pass.

[33mcommit 083f772285c07c841ff98831bcb7be01c670b644[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 11:28:07 2026 +0330

    feat: version tracking for retry/resume + remove session_id from progressbars
    
    Backend:
    - Added version column to pending_jobs and pending_companies (migration + DB schema)
    - reset_job increments version on each retry
    - Recovery marks stuck 'processing' jobs as failed with version bump
    - Worker passes previous session_id to mimo via --session for session resumption
    - Career intel sections pass previous session_id for retry continuation
    - _stream_mimo_output supports resume_session_id parameter
    - Updated all test fixtures to include version column
    
    Frontend:
    - ProcessingItem shows version (v1, v2...) instead of session_id
    - GenerationProgressCard: removed session_id from compact and full modes
    - Session ID only visible in Generation History drawer
    
    Tests: 267 backend + 23 frontend = all passing

[33mcommit 6748783b81b1adbb53d8821d8dbcde099cbd7fa8[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:58:56 2026 +0330

    fix: company card and drawer now show fit/success/overall scores consistently
    
    - Card: Grade badge + Fit/Success/Overall score badges
    - Drawer header: Grade + Fit/Success/Overall scores (matching card)
    - Scores tab: Full breakdown with Fit, Success, Overall sections
    - Shows calculation: Overall = Fit × 0.5 + Success × 0.5
    - Both read from company_intelligence.scores (same data source)
    - Added A- and D grade styles to PRIORITY_STYLES

[33mcommit 06cf7b0c488b8036b5b6a62edaf77571c720e481[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:53:34 2026 +0330

    fix: sync company card and drawer scores to use same data source
    
    - Both card and drawer now read visa_score, tech_match, career_score, priority
    - Drawer header shows Priority badge + Visa/Tech/Career scores (matching card)
    - Scores tab shows full breakdown: Visa, Tech Match, Career, International, Stability, Growth
    - Removed stale company_fit_score/company_success_score/company_overall_score references
    - Added ScoreRow helper with color-coded bars

[33mcommit 472e279914745bbde16b291a961099c1c43541b7[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:45:25 2026 +0330

    fix: show session_id for all items in generation history, always visible
    
    - Session ID now shown for every history item (shows '—' when null)
    - Increased max-width from 100px to 140px for better visibility
    - Slightly more opaque text color for readability

[33mcommit 6ef622fe99c2a7d2c73b0a4924acfcd6cb12864a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:40:09 2026 +0330

    revert: processed jobs/companies should NOT appear in processing column
    
    - Reverted 'done' status appearing in processing column
    - Jobs disappear from processing when complete, appear in processed via refreshJobs
    - Companies disappear from processing when complete, appear in processed via fetchCompanies
    - Processing column only shows: pending, queued, processing, failed

[33mcommit 28e4d9db405ff0c59a3af1f4613f9975cf6af5a5[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:34:43 2026 +0330

    fix: show completed jobs/companies in processing column + humanize history titles
    
    - JobsPage: include 'done' status in processing column filter
    - CompaniesPage: include 'done' status in processing column filter
    - Backend: map insight_type to human-readable labels (skills_intel -> Skills Intelligence)
    - GenerationHistoryDrawer: PAGE_SIZE 30 -> 100 for better coverage

[33mcommit fce698466503afb0fcc9f8ba6d915efd7d9c69c7[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:31:58 2026 +0330

    fix: increase generation history page size to show job/company processing
    
    - PAGE_SIZE 30 -> 100 to ensure job-processing and company-processing items are visible
    - All 4 sources now appear: career-intel, roadmap, job-processing, company-processing

[33mcommit ea46b1128f496b5b97e8147991cee97434e7dcd9[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:26:33 2026 +0330

    fix: update tailwind content glob and vite config for TypeScript files
    
    - tailwind.config.js: content glob now includes .ts/.tsx files
    - vite.config.js: test setup path updated to setup.ts
    - GenerationHistoryDrawer: fixed API URL, added full TypeScript types
    - CSS output restored from 9KB to 50KB (was being purged)

[33mcommit c2ac582b58841bb04ffc76f7ef8a712428c3e1a8[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 10:06:23 2026 +0330

    refactor: convert entire client codebase from JavaScript to TypeScript
    
    - Converted all 68 JS/JSX files to TS/TSX
    - Added tsconfig.json with bundler moduleResolution, allowJs, strict:false
    - Added TypeScript types to all hooks (useJobs, usePending, useCompanies, etc.)
    - Added TypeScript types to all components (props interfaces, state types)
    - Added unified generation history endpoint /api/generation-history
    - Added GenerationHistoryDrawer component with infinite scroll
    - Added history button in Header next to theme toggle
    - Fixed ProcessedCards test for TypeScript compatibility
    - Zero JS/JSX files remaining in client/src
    - Build passes, 23 frontend tests pass, 267 backend tests pass

[33mcommit b1ee23cb117c00e5e8ed31ec8c59e0dd5f60cce6[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 09:44:36 2026 +0330

    feat: show last-updated timestamp near each section title in career intel
    
    - Added SectionTimestamp component to tab triggers (shows in tab bar)
    - Added formatTimeAgo + Clock icon inside each section's header
    - Passes status prop from CareerIntelTab to all 6 section components
    - Skills tab maps to skills_intel status key
    - Timestamps show relative time (just now, 5m ago, 2h ago, 3d ago)
    - Failed sections show red timestamp with error tooltip

[33mcommit eecfc12635a8837f0ee2a04997bf22ecc80bc62c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 09:35:29 2026 +0330

    ci: add --cov and --cov-report to pytest for test coverage visibility

[33mcommit 203fb97c5f81c10f02427cd02705a28f6db47337[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 09:34:12 2026 +0330

    refactor: generate_all runs per-section prompts instead of monolithic combined prompt
    
    - generate_all() now runs each section's dedicated prompt sequentially
      (overview → opportunities → companies → market → networking → skills_intel)
    - Extracted _generate_section_internal() for single-section generation
    - Removed dead 'skills' entry from SECTION_PROMPTS (6 tabs = 6 prompts)
    - Fixed _db() overriding row_factory=None (broke _collect_*_data dict() calls)
    - Fixed SkillsIntelSection to read data?.skills_intel instead of data?.skills
    - generate_all() cleans up stale 'skills' entries from old combined prompt
    - Each section saves independently to DB; partial failures don't block others
    - Updated tests to match new per-section architecture

[33mcommit 241e2dd55648f3fb8024be5180b3037ad31018a9[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 05:12:43 2026 +0330

    fix: remove test warnings + add missing tables to test fixtures
    
    - skill_roadmaps.py: wrap _update_skill_progress DB calls in try/except
    - test_dashboard.py: add tech_stack, skill_aliases tables to fixture
    - test_dashboard.py: fix skill_relationships table columns
    - 306 tests pass, 0 warnings

[33mcommit 7e9de2b75a41c31421d422efe9bd83f4f2338061[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 05:03:42 2026 +0330

    fix: add missing skill_aliases table to test fixture + fix dict(row) errors
    
    - conftest.py: add skill_aliases table, add tags column to tech_stack
    - test_tech_stack.py: set conn.row_factory = sqlite3.Row for dict(row) calls
    - All 306 tests pass now

[33mcommit dbc0302d57e2d7295e4ab9166c277e288354dec2[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:58:15 2026 +0330

    ci: add GitLab CI with --cov for backend + frontend tests
    
    - .gitlab-ci.yml: backend-tests with pytest-cov, frontend-tests with vitest
    - pyproject.toml: add pytest config (testpaths, addopts)
    - Coverage reports: term-missing + HTML artifacts
    - Fixed test imports: dashboard → skill_roadmaps after file split
    - All 299 tests pass (7 pre-existing tech_stack failures unrelated)

[33mcommit b6a60e73d8b6523dcad692683d825fe69cfce162[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:54:51 2026 +0330

    refactor: rename dashboard.py → misc.py + level multi-select filter
    
    - Rename dashboard.py to misc.py (236 lines of misc endpoints)
    - Update app.py to import from misc.py
    - Add multi-select level filter: toggle buttons for Beginner/Basic/Intermediate/Advanced/Expert
    - Level filter uses Set for multi-select, clears with X button
    - Sort by level: Expert first, Beginner last, unset at bottom

[33mcommit 250a9af5f08df99e6f8d6de608def74a36cd1700[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:48:29 2026 +0330

    fix: useRef import, hasMore reference, get_status return format
    
    - Add useRef import to CareerIntelTab.jsx
    - Fix stale hasMoreRuns/hasMoreRoadmap references → hasMore
    - Fix get_status to handle new get_runs return format {items, total}
    - Add level sort option to skills

[33mcommit b626e57dc7479750b92310a708130ee037377cf3[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:40:39 2026 +0330

    refactor: split dashboard.py into 3 feature-based files
    
    Split 1491-line dashboard.py into focused modules:
    - dashboard.py (242 lines): insights, tech learning, cities, refresh
    - tech_stack.py (293 lines): skill CRUD, relationships, merge, hide/restore
    - skill_roadmaps.py (978 lines): roadmap CRUD, generation workers, progress
    
    Each file is a focused Flask blueprint with single responsibility.
    Updated app.py to register all 3 blueprints.

[33mcommit 8bed3308e19aa3f805ca3092bf4fa0724adae53c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:35:10 2026 +0330

    feat: infinite scroll history + delete flow + proficiency selector
    
    Infinite scroll:
    - Backend: get_runs and get_roadmap_jobs support offset + return total count
    - Frontend: HistoryDrawer loads 20 items initially, loads more on scroll
    - Badge shows total count (not just loaded count)
    - Drawer description shows total count
    
    Delete flow:
    - Skills must be hidden first (soft delete) before permanent delete
    - handleRemoveSkill now hides instead of deleting
    - handleDeleteSkill permanently deletes (only from Hidden section)
    - Hidden section shows restore + permanent delete buttons
    
    Proficiency level:
    - SkillDetailDrawer: clickable level buttons (Beginner/Basic/Intermediate/Advanced/Expert)
    - Level changes saved via PUT /api/tech-stack/{id}
    
    System tags in skill rows:
    - Proficiency level badge (Indigo)
    - Progress percent badge (Green/Gray)
    - Roadmapped badge (Emerald)

[33mcommit c9861e63f1db8e1153ac9fa3b0944243ebf5d135[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:27:36 2026 +0330

    feat: persistent generation tasks + proficiency level selector + system tags
    
    Persistent generation:
    - Save session_id to DB immediately when discovered (crash recovery)
    - Startup recovery hook: detect 'processing' runs, resume with --session
    - Shutdown no longer cancels generations (left as 'processing' for recovery)
    - Career intel and skill roadmap workers both recover on restart
    
    Proficiency level:
    - SkillDetailDrawer: clickable level buttons (Beginner/Basic/Intermediate/Advanced/Expert)
    - PUT /api/tech-stack/{id} accepts level changes
    
    System tags in skill rows:
    - Proficiency level badge (Beginner through Expert)
    - Progress percent badge (e.g. '75%')
    - Roadmapped badge (auto-set when roadmap exists)

[33mcommit 4bbbd6c81050b22b11121013ff5a1e5f86e5c5d6[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:22:27 2026 +0330

    feat: custom tags on skills + system roadmap tag
    
    - Add tags TEXT DEFAULT '[]' column to tech_stack (JSON array)
    - Migration adds tags column to existing databases
    - PUT /api/tech-stack/{id} accepts tags array
    - GET /api/tech-stack parses tags JSON to array
    - SkillDetailDrawer: tag editing UI (add/remove tags)
    - SkillsIntelSection: user tags shown as orange badges
    - System 'Roadmapped' tag auto-set based on roadmap data

[33mcommit 605d55686da7953b8c9215a45cc5d8f839d87334[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:12:28 2026 +0330

    fix: add missing Trash icon import in SkillsIntelSection

[33mcommit 6c068a30afd25b2a5f60f42ec79fef4c6acf6cca[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 04:05:20 2026 +0330

    refactor: unified skills card with sort and filter
    
    Replace 6 separate cards (Strengths, Roadmaps, AI-Detected, Custom,
    Gaps, Recommendations) with one unified skills list.
    
    New features:
    - Sort by: Strength, Roadmap Progress, Name, Market Demand
    - Filter by: Role (Strength/Gap/Rec/None), Source (Custom/AI),
      Roadmap (Has/No)
    - Each skill shows source tags: Custom (purple), AI (blue),
      Strength (green), Gap (red), Rec (primary)
    - Inline roadmap progress bar or Generate button per skill
    - Category tabs preserved for filtering
    - Merge mode works across unified list
    - Hidden skills section stays at bottom
    
    No DB or prompt changes needed — tech_stack is already the
    canonical source of truth.

[33mcommit 44324285bff378138715888516084b76e68ef656[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:56:41 2026 +0330

    test: comprehensive career_intel unit tests (82% coverage)
    
    59 tests covering: _emit_progress, _cleanup_stale_runs, is_running,
    get_progress, cancel_run, _start_run/_complete_run, _save_insight,
    _generate_all, generate_section, generate_skills_intel, get_latest,
    get_runs, _run_mimo_prompt. Fixed mock paths for MimoRunner.

[33mcommit fd4a4ccaf03a349bbf3cab5d9564f964370d2cb0[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:47:29 2026 +0330

    fix: history badge count includes roadmap jobs
    
    Badge showed only career intel runs count, but drawer showed
    career intel + roadmap jobs combined. Now badge matches drawer.

[33mcommit 8c68d1c755de6e9737f4a0d9145d74edf46f62da[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:25:26 2026 +0330

    feat: show job type in roadmap history entries
    
    Roadmap entries now show 'generate: Python', 'extend: Docker',
    'finegrain: PostgreSQL' instead of just 'roadmap: Python'

[33mcommit 1053f0bb9a8d62f25a983e24c09fbb130aa13dd2[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:24:32 2026 +0330

    feat: show roadmap generation jobs in history drawer
    
    - Add GET /api/skill-roadmap-jobs endpoint returning recent skill_roadmap_jobs
    - Update fetchRoadmapJobs to use new endpoint instead of progress/all
    - HistoryDrawer now shows both career intel runs and roadmap generation jobs
      with proper status, session_id, timestamps, and error messages

[33mcommit 7d50faa6b378158cd8c0f1e2af21afc1335994aa[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:22:24 2026 +0330

    fix: terminate button not working after MimoRunner refactor
    
    - Store process_key in _current_run so cancel_run() can find the process
    - cancel_run() now uses ProcessManager.get(key) + cancel(handle) to kill
      the mimo subprocess managed by MimoRunner
    - Fallback to raw process.terminate() still works for legacy paths

[33mcommit c40e006d57f3126b411bed7447927784e7eba038[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:19:26 2026 +0330

    fix: session_id discovery, timeout, and generate_all skills handling
    
    - Fix sessionID case mismatch in MimoRunner (mimo outputs 'sessionID' with capital D, was only checking 'sessionId')
    - Increase default timeout from 300s to 600s, generate_all to 900s
    - generate_all() now runs dedicated skills_intelligence prompt after combined prompt
    - Skip minimal 'skills' from combined prompt, save full skills_intel report instead

[33mcommit cd69faa7a131f31acdf1ad69b5efe1a20ea857e9[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:15:16 2026 +0330

    fix: merge WebSocket progress updates to preserve session_id
    
    setProgress(data) was replacing the entire state, so the first
    WebSocket event (running: true, no session_id yet) would overwrite
    any existing session_id. Now merges with spread operator so session_id
    and other fields persist across events.

[33mcommit 8f9e1325f787c518e7ddd62aa85ce265260f1396[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:13:59 2026 +0330

    fix: show progress bar immediately on refresh click
    
    Optimistically set progress.running=true in refreshSection/refreshAll
    before the WebSocket event arrives. Previously, the progress bar only
    appeared after the backend thread started and emitted the first
    career_intel:progress event — causing a visible delay.

[33mcommit cae8c76c0c1997b1d296550fad4b4dd5296f853d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:09:24 2026 +0330

    feat: separate career intel prompts per tab
    
    - Split monolithic career_intelligence.txt into 6 per-section prompts:
      overview, opportunities, companies, market, networking
    - Skills tab uses dedicated skills_intelligence.txt (full report)
    - Add SECTION_PROMPTS mapping in career_intel.py
    - Refactor generate_section() to use per-section prompts
    - generate_all() saves skills output as skills_intel for frontend compatibility
    - Single-section refresh now runs only that section's focused prompt
    - All generation types tracked in HistoryDrawer (no changes needed)
    - Add 6 new tests for section prompt routing
    - Update ARCHITECTURE.md prompt organization and data flows

[33mcommit 76d2cd1564d01f1b3dcdd71ae57d1ec2774138c0[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sat Jul 25 03:01:53 2026 +0330

    fix: career intel streaming session_id, empty skill categories, hidden skills layout
    
    - Refactor _run_mimo_prompt to use MimoRunner (streaming) instead of subprocess.Popen (blocking)
    - Fix MimoRunner session_id discovery bug (fallback prevented real discovery)
    - Emit progress event immediately when session_id discovered
    - Extract resolveSkillCategory/filterByCategory domain functions for category fallback
    - Move Hidden Skills section to end of SkillsIntelSection
    - Add coding standards to ARCHITECTURE.md (OOP/SOLID/DDD/TDD backend, feature-based frontend)
    - Add tests: 5 backend streaming tests, 11 frontend skills domain tests

[33mcommit 2b5a291185d21fc6969d3f0725128684c1d33f8d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 07:00:52 2026 +0330

    fix: pytest

[33mcommit 3d106f8cbf00bd83cfbd2098442927d848fea67a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 06:37:51 2026 +0330

    ci: add GitHub Actions workflow for backend + frontend tests
    
    - Backend: pytest with uv on Python 3.12
    - Frontend: npm ci + npm run build on Node 20
    - Triggers on push/PR to main

[33mcommit 2122d56521a9ca997be7e62683fc848908c6940a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 06:26:21 2026 +0330

    docs: add comprehensive root README.md

[33mcommit 8e1afd3fef433a8f3d803198cc3dd80bb481d411[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 06:24:23 2026 +0330

    docs: update changelog, architecture, test structure for skill system

[33mcommit a8bb986b579fcb4a554d0450c3829faab2f3f32a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 06:20:56 2026 +0330

    chore: update .gitignore for coverage, logs, pid files, generated schema

[33mcommit 85c4aa9a6d0efc601cee3808328fd17eeed5001c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 06:17:57 2026 +0330

    feat: skill aliases table, rename/remove/hide, collapsible add skill, roadmap checks
    
    - Add skill_aliases table (proper two-table design per spec)
    - Merge creates alias records instead of deleting skills
    - Rename skill endpoint updates all references
    - Delete skill removes all its aliases
    - Skill rows show Hide (yellow) and Remove (red) buttons
    - Remove shows confirmation with alias count
    - SkillDetailDrawer: rename input, checkable roadmap items, merged variants
    - Collapsible Add Custom Skill input inline with category tabs
    - Learning Roadmap in drawer is collapsible with tree items
    - Consistent tab styling across all drawers (bg-muted)
    - Market Intelligence: scrollable cities, compact right sidebar
    - Fixed JSX errors (stray }), missing Input/PencilSimple imports

[33mcommit 74bbe60f9b49fa734da8fa2062ca332809888765[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 04:26:12 2026 +0330

    feat: skill taxonomy, relationships, details drawer, prompt folderization
    
    - Add skill categories (technical, engineering, professional, domain, career)
    - Add skill_relationships table (related, similar, parent, child, alternative)
    - Add SkillDetailDrawer with category, confidence, evidence, relationships
    - Redesign SkillsIntelSection: two-column layout, category filtering,
      clickable stat cards, merge across all sections (Strengths/Gaps/Recs)
    - Update AI prompt to output structured skill data with categories
    - Add endpoints: hidden list, restore, skill relationships CRUD
    - Folderize prompts: career_intel/, skill_roadmaps/, job_processing/,
      company/, resume/ (features_refactors/ untouched)
    - Reorganize tests to mirror server structure
    - Add 12 new tests: taxonomy, hidden restore, relationships
    - Market Intelligence: compact right sidebar, scrollable cities

[33mcommit 5741e2c687c3160a36d4dd1b3213d77abf823678[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 03:51:16 2026 +0330

    chore: remaining changes — queue refactor, skill prompts, architecture docs
    
    - Queue module refactor (queue.py)
    - Companies/pending blueprint updates
    - Skill roadmap generation prompts (extend, finegrain, generate)
    - Worker architecture documentation
    - sql_roadmap.json schema reference
    - Vite config and App.jsx updates
    - Removed deprecated start.sh

[33mcommit 8ada841e5c0d076005c53c47d577bdd25380562c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Fri Jul 24 03:50:09 2026 +0330

    feat: WebSocket real-time updates, skill hide/merge, session_id extraction
    
    - Real-time WebSocket for pending jobs/companies/career-intel progress
    - Session ID extraction from mimo output (all 5 variants + fallback generation)
    - Broadcast logging with [ws] prefix for audit trail
    - Skill management: hide redundant skills, merge duplicates via drag-and-drop
    - Skills categorized: Custom (user-input), AI-analyzed, AI-detected
    - Fixed ProcessingItem workflow_log JSON.parse crash
    - Removed career-intel polling (WebSocket replaces it)
    - Market Intelligence layout: Countries moved to compact right sidebar
    - Shared test_db fixture, 27 new tests (broadcast, skill management, broadcaster)

[33mcommit 14814e633dba4dd27946132ee0d2216df2d1975a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 20:08:25 2026 +0330

    feat: graceful shutdown, start.sh, CLI cleanup, session_id improvements
    
    - Add signal handlers (SIGTERM/SIGINT) for graceful process termination
    - Register subprocesses for cleanup on shutdown
    - Reset stuck jobs in DB on shutdown
    - Create start.sh script with start/stop/status commands
    - Add CLI cleanup command (--kill-mimo, --reset-jobs, --reset-roadmaps, --all)
    - Add session_id display with default 'session pending' text when null
    - Update session_id parser to try multiple key formats
    - Add debug logging for session_id parsing
    - Create CLI.md documentation
    - Update GenerationProgressCard with default session_id text

[33mcommit b7be933aded47f725228e17fb9e9c6d8f6fececb[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 19:42:38 2026 +0330

    feat: add session_id display to job and company processing cards
    
    - Add session_id to ProcessingItem status display (all non-done statuses)
    - Add session_id to CompanyProcessingItem status display (all non-done statuses)
    - Click to copy session_id for external interaction
    - Both components show session_id for pending, queued, processing, and failed statuses

[33mcommit 0f7170320df2d2bc11c04feaa163869aa1ed50af[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 19:34:45 2026 +0330

    feat: shared GenerationProgressCard component with session_id display
    
    - Create shared GenerationProgressCard component with compact/full modes
    - Show session_id with copy-to-clipboard in all progress bars
    - Update SkillsIntelSection to use shared component
    - Update SkillRoadmapDrawer to use shared component
    - Update CareerIntelTab IntelProgressCard to use shared component
    - Add session_id to career_intel progress endpoint
    - All progress bars now show session_id for external interaction

[33mcommit 96fe0be012104f1122556d1aef589b9e1fe6d5e4[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 19:17:41 2026 +0330

    fix: complete topic→roadmap rename across entire codebase
    
    - Rename TopicNode→RoadmapNode, fetchTopics→fetchRoadmap
    - Rename topicId→itemId in handleToggle
    - Rename topicProgress→roadmapProgress in all components
    - Rename skillTopicProgress→skillRoadmapProgress in App.jsx
    - Rename checked_topics→checked_items in prompt and backend
    - Update all comments to use roadmap terminology
    - Add session_id display in SkillRoadmapDrawer progress bar
    - All syntax verified clean

[33mcommit 2869748ae850393c07ac75c84bbf5335b2bc3d0b[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 19:01:19 2026 +0330

    fix: complete topic→roadmap rename and fix mode error
    
    - Fix mode undefined error in _run_generate_worker (use 'generate' instead of mode)
    - Rename all remaining topic references to roadmap in backend
    - Update prompt file skill_roadmaps.txt to use roadmap terminology
    - Rename frontend variables: topicProgress→roadmapProgress, topics→roadmapItems
    - Fix API response key mismatch (roadmap vs roadmapItems)
    - Add session_id to progress endpoint response
    - All syntax verified clean

[33mcommit 10d1bb8a9f80bba312cfb514457280a14fa80fef[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 17:02:15 2026 +0330

    fix: rename skill_topics to skill_roadmaps across all layers
    
    - Rename DB tables: skill_topics → skill_roadmaps, skill_topic_progress → skill_roadmap_progress, skill_topic_jobs → skill_roadmap_jobs
    - Rename API endpoints: /api/skill-topics/* → /api/skill-roadmaps/*, /api/skill-topic-progress/* → /api/skill-roadmap-progress/*
    - Rename frontend component: SkillTopicDrawer.jsx → SkillRoadmapDrawer.jsx
    - Rename prompt file: skill_topics.txt → skill_roadmaps.txt
    - Update all frontend API URLs to match new routes
    - Fix skillsWithProgress undefined variable error
    - Fix non-existing company navigation with Add button
    - All syntax verified clean

[33mcommit 5e17243ed225e971b81b2d43505119959c666d8c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 16:49:02 2026 +0330

    feat: Skills Intelligence Engine with interactive roadmap system
    
    - Skills Intelligence prompt with 9 analysis layers (career_intel)
    - Skill Roadmap system: DB tables (skill_roadmaps, skill_roadmap_progress, skill_roadmap_jobs)
    - Backend: CRUD, generate, extend, finegrain, cancel endpoints with background workers
    - Progress tracking persisted to DB, survives page refresh
    - Frontend: SkillRoadmapDrawer with nested tree, checkboxes, progress bars
    - Parent tick/untick propagates to all children
    - Progress counts only leaf nodes, latest version only
    - Generated roadmaps section with progress per skill
    - Custom skills section for user-added skills
    - Company cards clickable with Add button for non-existing companies
    - Collapsible sidebar with Career Intel sub-tabs
    - URL hash sync with tab/sub-tab state
    - History drawer as Sheet component
    - Resume tab moved to Settings section
    - Analysis History as Sheet drawer with header button

[33mcommit a16f816b309625304e23341548cd0915fd1fb379[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 13:17:15 2026 +0330

    Remove legacy Intelligence tab and all related parts
    
    - Deleted intelligence components (IntelligenceTab, 6 section components)
    - Deleted useIntelligence hook and its export
    - Deleted intelligence blueprint and /api/intelligence endpoints
    - Deleted legacy worker functions (_save_analysis, _run_analysis_prompt, _update_*_analysis)
    - Deleted legacy prompts (analysis_update.txt, dashboard_update.txt, skills_update.txt)
    - Removed stream_server._update_dashboard_insights async function
    - Updated CLI commands to use career_intel service
    - Updated dashboard refresh routes to delegate to career_intel
    - Updated Header.jsx FEATURES array to show Career Intel instead of Intelligence
    - Updated App.jsx to remove Intelligence tab from routing and rendering

[33mcommit d8095eabaca36ee24f1f1bdf26287169aa83d0b8[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 12:49:25 2026 +0330

    Add Career Intelligence system with 6 sections, concurrency control, cancel support, and docs
    
    - Backend: career_intel.py service with threading lock, Popen-based subprocess termination, stale run cleanup, session_id parsing
    - API: 8 endpoints including /cancel, /progress, /status, /runs
    - Frontend: CareerIntelTab with progress card, terminate button, error banner, history list, 6 section tabs
    - DB: career_insight_runs (with session_id) and career_insights tables
    - Prompt: career_intelligence.txt for AI analysis
    - Docs: Concise documentation structure
    - Removed MEMORY.md (contents moved to docs/)

[33mcommit 83316fda30b2cc6431eb38277327f7fc2e17859f[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 23 00:35:52 2026 +0330

    Add score filter, fix company links, highlight company connections in job cards
    
    - Add multi-select score filter (A++ through E) to jobs page with backend support
    - Fix company links race condition: store links in pending_companies before processing
    - Worker moves links from pending_companies to company_links after company save
    - Add predefined link titles (LinkedIn, Website, Careers, GitHub) in company forms
    - Add inline notes/links editing on pending company cards (add/edit/remove)
    - Fix Market Intelligence stale data: use jobsTotal instead of paginated jobs.length
    - CompanySection fetches all jobs for accurate company rankings
    - Highlight linked companies on job cards with clickable badge
    - Show linked company in JobDrawer header with navigation to company drawer
    - Add PUT endpoints for pending company notes and links
    - Parse links from JSON in pending companies GET and stream endpoints
    - Add Array.isArray safety checks for notes/links in ProcessingItem components

[33mcommit 4d9b6a2f8f1a854297e2c3b1563409dca30709f5[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 20:53:51 2026 +0330

    Replace custom toast with Sonner notification component
    
    - Install sonner and next-themes packages
    - Create Toaster component with design token integration
    - Position notifications at bottom-left
    - Update useResume to use sonner directly
    - Update useToast hook to use sonner
    - Add ThemeProvider for theme support
    - All notifications now use consistent Sonner component

[33mcommit 4c0be0b8c915d1330c9f3e6beeec62a72d073fea[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 20:43:26 2026 +0330

    Unify all toast notifications to use global toast system
    
    - Move main toast position from center to bottom-left
    - Update ResumeTab to use global toast via window.dispatchEvent
    - Remove local toast state from ResumeTab
    - All notifications now appear consistently in bottom-left corner

[33mcommit 34ba545d83395fba2f007ad680fb617c0ad1ac5f[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 20:35:56 2026 +0330

    Add per-section analysis timestamps and fix refresh logic
    
    Backend:
    - Update _save_analysis to track per-section timestamps in metadata.lastUpdated
    - Add /api/intelligence/timestamps endpoint for section timestamps
    - Fix section refresh endpoints to call specific worker functions instead of unified
    - Add _update_market_analysis and _update_opportunity_analysis worker functions
    
    Frontend:
    - Add fetchTimestamps and getLastUpdated to useIntelligence hook
    - Update IntelligenceTab to show section-specific last updated timestamps
    - Show relative timestamps (e.g., '5m ago', '2h ago')
    - Pass timestamps to each section component
    - Fix refreshing state keys to match section names

[33mcommit 7012a73303a17d54f764120a96ef47e4417fa2e9[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 19:16:07 2026 +0330

    Add View All Jobs link to CompanyDrawer
    
    - Add onViewAllJobs prop to CompanyDrawer
    - Show 'View All Jobs' button when company has jobs
    - Navigate to jobs page with company filter pre-applied
    - Close company drawer and switch to jobs tab on click

[33mcommit ea43e2b498be04f22131947a0a761b71e33169d2[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 19:14:01 2026 +0330

    Extract custom hooks from App.jsx to reduce complexity
    
    - Create useJobs hook for job fetching, filtering, sorting, pagination
    - Create usePending hook for pending job management with SSE stream
    - Create useCompanies hook for company data and pending companies SSE
    - Create useWorkflow hook for WebSocket workflow management
    - Create useIntelligence hook for intelligence data and refresh handlers
    - Create useResume hook for resume/cover letter generation
    - Create useToast hook for toast notifications
    - App.jsx reduced from 502 to 200 lines
    - All functionality preserved, build passes

[33mcommit 57f2f3f5054cfe2144799a4cae4e56719a8a9c76[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 19:02:04 2026 +0330

    Refactor component structure into feature-based folders
    
    - Move components into feature folders: layout/, jobs/drawer/, resume/, rules/, shared/
    - Extract 5 inline tab components from JobDrawer into separate files (DetailsTab, StructuredTab, SummaryTab, DocumentsTab, CompanyTab)
    - Create shared DrawerComponents.jsx with reusable Section, Field, TagList, ScoreBadge, TabHeader
    - Move shared utilities to shared/: ProcessedCards, ProcessingItem, ResumePreview, MultiSelect, TechCards
    - Move layout components to layout/: Header, Sidebar
    - Refactor Header with feature navigation tabs and improved stats display
    - Align CompanyDrawer design with JobDrawer (colors, sizes, tab headers)
    - Update all imports across the codebase
    - Add .sentry-native/ to .gitignore

[33mcommit 25d51c176a14081da8bdaa3fc9d39d3e6535c38c[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 18:42:32 2026 +0330

    Refactor rule system to entity-based scopes and improve company jobs UI
    
    - Refactor preferences table: add scope column, migrate from rule_type-based filtering to entity-based rule groups (SHARED/JOB/COMPANY_PRODUCT/COMPANY_RECRUITING)
    - Consolidate job rules from 32 to 6 focused rules, company rules to 4 per entity type
    - Update all backend query filters from rule_type IN to scope IN
    - Improve CompanyJobsTab with action buttons (open drawer, navigate to jobs page)
    - Update global.css with warmer color palette and design token refinements

[33mcommit dbbc22586185eb2162a5f3b4c7640c4bae25d5ab[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 17:17:21 2026 +0330

    Add company type classification, recruiter scoring rules, and improve error messages
    
    - Add company_type field classification (PRODUCT_COMPANY, RECRUITING_AGENCY, STAFFING_COMPANY, CONSULTING_COMPANY, UNKNOWN)
    - Add 4 new recruiter-specific scoring rules (network_value, market_access, profile_alignment, activity_and_opportunity)
    - Update extraction prompt to detect company types from signals
    - Update analysis prompt with type-aware scoring guidelines
    - Refactor _load_rules() to load type-specific rules based on company_type
    - Improve error messages in company_worker.py and worker.py with human-readable step labels
    - Add HTTP error handling (404, 403, 503) with descriptive messages
    - Make error text copyable in CompanyProcessingItem and ProcessingItem UI components
    - Reorganize prompt files into features_refactors/ directory

[33mcommit 2f06f16921826edc7d23fe41e9584fb04951d1e2[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 16:47:04 2026 +0330

    Add refactoring prompt documents for progress history
    
    - Add 03_refactor_rule_system.txt: Rule system refactoring with shared/job/company categories
    - Add 04_refactor_company_process_and_its_score.txt: Company scoring and processing pipeline
    - Add 05_refacotor_company_notes_and_links.txt: Notes and links management system

[33mcommit d650ab6ace41ae5d937c4b8710ec9883300274ae[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 16:40:58 2026 +0330

    Add job count to company card/drawer and fix extraction for multi-note input
    
    - Add job_count field to company API endpoints (get_companies, get_company)
    - Display job count badge on CompanyCard when jobs are linked
    - Show job count in CompanyDrawer header and Jobs tab
    - Fix _extract_company_info to properly handle multi_note content format
    - Add logging for extraction failures to help debug issues

[33mcommit 5e618acf32a453e6f7f2d09f2deaf5cbabe23882[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 16:33:40 2026 +0330

    Add links support to company creation and processing flow
    
    - Update CompaniesPage to show both Notes and Links sections when adding a company
    - Add LinkItem component for displaying links in the input area
    - Update handleSubmit to send both notes and links when creating a company
    - Update reprocess endpoint to reset link statuses for reprocessing
    - Update company_worker to reset link statuses at start of processing
    - Maintain backward compatibility with existing notes-only flow

[33mcommit d78318c797b8046c6e4567de04d90765ca29a1c9[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 16:29:31 2026 +0330

    Refactor company notes and links with dedicated link management
    
    - Add company_links table for storing URLs with title, description, and status
    - Add CRUD API routes for company links (GET, POST, PUT, DELETE)
    - Refactor CompanyNotesTab to separate Notes and Links sections
    - Update company processing pipeline to fetch and process company links
    - Update link status (pending/processed/failed) during processing
    - Maintain backward compatibility with existing notes structure

[33mcommit 07ea20590ba95a74a5e6111946362f170a2a94b5[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 16:17:42 2026 +0330

    Refactor company processing with new scoring system and tabbed drawer UI
    
    - Update company_analyze.txt with three new scores: company_fit_score, company_success_score, company_overall_score
    - Add grade calculation (A++/A+/A/B/C/D) and positive/negative factor explanations
    - Refactor CompanyDrawer to use three main tabs: Original Notes, Intelligence, Scores
    - Update Job Drawer Company tab to show linked company intelligence and scores summary
    - Maintain backward compatibility with existing data structure

[33mcommit a46f0d4e2c71fb4a5247f03b3a625eeed4cc3906[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 15:52:09 2026 +0330

    Refactor rule system to support shared/job/company rule categories
    
    Extend the scoring rule architecture from two categories (fit/success) to
    three rule types (shared/job/company) with independent score weights:
    
    - Add rule_type column (shared/job/company) and score_weight column
    - Shared rules apply to both job and company scoring (visa, location, culture)
    - Job rules apply only to job scoring (tech stack, role alignment)
    - Company rules apply only to company scoring (quality, engineering culture)
    - Update _load_rules() in worker, stream_server, company_worker with context filtering
    - Update frontend RulesTab to 3-column layout (shared/job/company)
    - Update rules API, CLI, and cover letter generation for new schema
    - Migration handles backward compatibility for existing databases

[33mcommit 87fc25557a42f6df36bbd6bd706d804a9994bde3[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 15:36:11 2026 +0330

    Fix missing Response import in companies blueprint

[33mcommit 4798322f0b69424ad418d4109c5125186b621809[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 15:35:18 2026 +0330

    Refactor app.py (1862 lines) into Flask blueprints with clean architecture
    
    Break the monolithic app.py into feature-based modules following
    SOLID principles and Flask blueprint pattern:
    
    New structure:
      app.py         (59 lines)  - Slim entry point, wires blueprints
      config.py      (15 lines)  - App configuration (DB_PATH, paths)
      database.py    (32 lines)  - Consolidated DB access with retry logic
      migrations.py  (193 lines) - All schema migrations and data backfills
      utils.py       (61 lines)  - Shared helpers (normalize_url, mask_pii, etc.)
    
    Blueprints (route handlers grouped by domain):
      jobs.py        - Job CRUD, rescore, reprocess, summaries
      resumes.py     - Resume + LinkedIn profile CRUD, generation
      pending.py     - Pending job queue management, SSE streams
      companies.py   - Company intelligence, notes, pending companies
      intelligence.py - Analysis/intelligence API endpoints
      rules.py       - Scoring rules CRUD
      dashboard.py   - Dashboard insights, tech stack, cities, refresh
      static.py      - React SPA catch-all serving
    
    Each blueprint is self-contained with its own routes. The entry point
    stays minimal: config -> migrations -> queue -> register blueprints.

[33mcommit 7aeb1c6192fb546a9941ee39f27d2c2614af8573[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 15:10:42 2026 +0330

    Refactor client components into feature-based folder structure
    
    Reorganize flat components/ directory into feature-based modules:
    - companies/: CompaniesPage, CompanyCard, CompanyDrawer, CompanyJobsTab,
      CompanyNotesTab, CompanyProcessingItem, ScoreBar
    - intelligence/: IntelligenceTab + 6 extracted sections (Market, Opportunity,
      Strategy, Skills, Company, Networking)
    - shared/: ConfirmDialog, DuplicateJobDialog, WorkflowTerminal
    
    Extract bloated files into focused components:
    - IntelligenceTab (920 lines) split into 7 files
    - CompanyDrawer (499 lines) extracted CompanyJobsTab, CompanyNotesTab, ScoreBar
    - Shared ConfirmDialog extracted to replace duplicated AlertDialog code
    
    Build compiles successfully.

[33mcommit 11e3bf0184f3bbc314a2e630be1ea24d6b8cf338[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 12:36:51 2026 +0330

    Add deep linking: job/company drawers openable by URL hash
    
    - #jobs/123 opens job drawer for job #123
    - #companies/5 opens company drawer for company #5
    - URL updates when drawers open/close
    - Auto-opens drawers on initial page load from URL
    - Both tabs support deep linking via hash routing

[33mcommit 058fbb36c6d0c977b12264d8f4828026cc8dc053[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 12:10:31 2026 +0330

    Fix job processing: add missing company_id to INSERT (42 cols, 41 values)

[33mcommit 95668dedef8a78f709b6bce6d3121986cf8545bf[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 12:07:07 2026 +0330

    Add company notes management in drawer (add/edit/delete for reprocessing)
    
    - Add notes column to companies table
    - CRUD API endpoints for company notes
    - Notes tab in CompanyDrawer with add/edit/delete UI
    - Notes flow: pending_companies -> companies -> reprocess
    - Reprocess uses company notes for better AI analysis

[33mcommit 47e939df3f2d37abc8cb51fce67f219cd3638cdc[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 11:36:46 2026 +0330

    Company analysis now uses fit/success scoring rules from DB
    
    - Add _load_rules() to company_worker.py (reads preferences table)
    - Pass rules to company_analyze prompt
    - Scoring guidelines reference specific FIT and SUCCESS rules
    - tech_match scored against python_primary, backend_core, database_match rules
    - visa_score scored against visa_requirement, visa_path_clarity rules

[33mcommit d34f94419f949a209a850b7ecc67e6340f9fa814[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 11:25:51 2026 +0330

    Refactor App.jsx: extract components and organize into folders
    
    - Extract JobsPage (215 lines) from App.jsx — full jobs tab with queue + filters
    - Extract WorkflowTerminal (88 lines) — workflow log viewer
    - Extract DuplicateJobDialog (39 lines) — duplicate job handling
    - App.jsx reduced from 779 to 457 lines (41% smaller)
    - Create component folders: jobs/, shared/
    - Fix .gitignore: /jobs/ (root-level only) to not block components/jobs/
    - Move feature spec to prompts/features/

[33mcommit ca1b95e5b6d28236f182591dc345896492e3d3b0[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 11:00:57 2026 +0330

    Add Company Intelligence feature with job-company linking
    
    - Multi-note input system (URLs + text notes) for company research
    - AI-powered company processing pipeline (fetch, extract, analyze, save)
    - Company page with search, sort, filter, and processing queue
    - Company drawer with 8 intelligence tabs (culture, visa, tech, career, etc.)
    - Job-company linking: link/unlink jobs to processed companies
    - Company tab in job drawer with company search/select
    - Jobs tab in company drawer showing connected positions
    - Disable rescore-all and reprocess-all from jobs header
    - Fix core/db.py path to use single DB at app/server/db/jobs.db
    - Queue system supports both pending_jobs and pending_companies

[33mcommit 22c47b09e5ea92669d32cd6c678d53cd3b751902[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 01:53:47 2026 +0330

    Remove unused DashboardTab.jsx (replaced by IntelligenceTab)

[33mcommit cef4fe2f67455027e4fa06431ed7f69d458bf340[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 01:50:19 2026 +0330

    Fix temp folder: consolidate to single TMP_DIR at repo root
    
    - Fix PROJECT_ROOT in worker.py to resolve to repo root (3 levels up from services/)
    - Remove duplicate app/tmp directory, keep only root tmp/
    - Ensures mimo writes results to correct temp location

[33mcommit 168c05070108c22d04f9d39f53b358ee367b434d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 01:05:44 2026 +0330

    Add Career Intelligence module with 6 sections
    
    - Market Intelligence: jobs by city/country/role, tech demand, score/visa distribution
    - Opportunity Radar: fit×success matrix, top opportunities with scores and actions
    - Application Strategy: action items, urgency, goals, strengths
    - Skill Intelligence: tech stack, learning priorities, ROI, level distribution
    - Company Intelligence: rankings by score, visa sponsorship, top cities
    - Networking Intelligence: LinkedIn targets, recruiter/engineer searches
    
    Backend:
    - Extend analysis_update.txt prompt with market + opportunity sections
    - Add /api/intelligence endpoints (GET/POST for all sections)
    - Worker saves under page='intelligence' with fallback to 'analysis'
    
    Frontend:
    - Rename Dashboard → Intelligence tab
    - Install recharts for chart support
    - New IntelligenceTab.jsx with 6 sub-tabs, per-section refresh, AI insights
    - Each section has Observation/Evidence/Impact/Action format insights
    - Single mimo call generates all 6 sections

[33mcommit 9bb2d953fe11f6acb338cd4bc268965ed45ed528[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 22 00:32:59 2026 +0330

    Refactor scoring system: 3 independent scores (fit/success/overall)
    
    - Add fit_score, success_score, overall_score numeric columns (0-100) to jobs table
    - Overall score = (fit × 0.6) + (success × 0.4), stored in DB
    - Update step8_score.txt prompt to request numeric scores from mimo
    - Worker parses numeric scores, computes overall, stores all three
    - API sorting uses overall_score column directly
    - Frontend displays 3 scores: Overall (primary), Fit (F:), Success (S:)
    - JobDrawer shows 3-column score header
    - Rename workflow step 'score' → 'analyze', 'resume' → 'save'
    - Default sort: newest first (created_at desc)
    - Remove alembic (inline migrations in db.py/app.py handle schema)
    - DB backup saved to db-back/

[33mcommit cf05d4174b1128e02c01ac0861cac5c59b9c1281[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 14:00:35 2026 +0330

    Fix 8 missing imports in App.jsx: TrendUp, HouseSimple, PaperPlaneRight, Confetti, Sheet, SheetContent, SheetHeader, SheetTitle

[33mcommit 14b82b991efad17e6f975fa53c5ce54af1a02714[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 13:17:28 2026 +0330

    Fix missing ChartBar import in App.jsx

[33mcommit 0e13459f473bc1172b98cfca1835673069075f62[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 13:07:03 2026 +0330

    Extract components from App.jsx to reduce bloat
    
    - Sidebar.jsx (30 lines) — navigation sidebar
    - Header.jsx (26 lines) — top bar with stats
    - JobDrawer.jsx (290 lines) — job detail drawer with all tabs
    - DashboardTab.jsx (766 lines) — dashboard with Overview/Strategy/Networking/Skills sub-tabs
    
    App.jsx: 1820 → 745 lines (59% reduction)
    Total: 1857 lines across 5 files (same code, better organized)

[33mcommit ba48182e65923bc0a1ab2d0c42100dde7783b6ef[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 12:07:09 2026 +0330

    Auto-collapse empty Processing Jobs sections with 0 indicator
    
    - Show all sections (Pending, Queued, Processing, Failed) always
    - Empty sections auto-collapse to header-only with reduced opacity
    - Click on empty section does nothing
    - Badge shows count; 0 shown in muted style

[33mcommit 04e9bd588179ccb37acf9d4b7a4568d46d752eb9[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 11:54:50 2026 +0330

    Enforce global 2-job concurrency limit at DB level
    
    - _pick_and_claim() now counts actual processing jobs in DB before
      claiming, not just in-memory _active_count
    - _worker_loop() syncs _active_count with DB state each iteration
      to prevent drift from crashes or race conditions
    - Concurrency limit applies to all sources: process, rescore, reprocess

[33mcommit 0e3701daee9c9b4033b89df4680a3c474d774669[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 11:49:33 2026 +0330

    Fix worker.py DB path after folder restructuring
    
    _file_dir resolved to services/ instead of server/, so DB_PATH
    pointed to non-existent services/db/jobs.db. Fixed by computing
    _server_dir = _file_dir/.. to resolve relative to server root.

[33mcommit 3f93e69cdbb537f6d9fcdfce600e72cb255f54e2[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 11:39:16 2026 +0330

    Clean up legacy inline migrations, add migrate.sh helper
    
    - Slim down _ensure_db_schema() to minimal backward-compat safety net
    - All schema changes now go through alembic migrations
    - Add migrate.sh for easy migration workflow (new/upgrade/downgrade/history)
    - Future DB changes: use './migrate.sh new "description"' then edit & upgrade

[33mcommit af3d33635752e3a3d0ce19949a0512e50cbc3072[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 11:36:55 2026 +0330

    Update start.sh to run alembic migrations before starting services

[33mcommit 123c6e98907fb0e93a7ada27ff77e58ef8bf4ccb[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 11:35:24 2026 +0330

    Add alembic migrations and restructure server into folders
    
    Alembic:
    - Install alembic + sqlalchemy dependencies
    - Initialize alembic with SQLite configuration
    - Create 001_init_schema migration capturing current DB state
    - Stamp existing DB at revision 001
    
    Server restructuring (by layer):
    - core/ — db.py (database helpers), queue.py (queue manager)
    - services/ — worker.py (processing pipeline)
    - scripts/ — analyze_jobs, backfill, normalize, process_pending, trigger
    - api/ — (prepared for future route extraction)
    - Updated all imports across app.py, cli.py, worker.py, queue.py

[33mcommit 95317ec169ef432ac940af7de0908da4e0076c1a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Tue Jul 21 11:17:33 2026 +0330

    Add apply tracking feature: apply_time, response_time, response_status fields
    
    - Add 3 DB columns with auto-migration in _ensure_db_schema()
    - PUT /api/jobs/<num> endpoint for updating job fields
    - Filter by response_status and applied-only in GET /api/jobs
    - Sort by apply_time and response_time
    - Applied badge on job cards (green PaperPlaneRight icon)
    - Response status badges (Interview=green, Rejected=red)
    - Drawer Application Tracking section with date pickers and status select
    - Filter bar: Status MultiSelect + Applied toggle button

[33mcommit bf29c0861e894709ac121f2f249b44fc4e5f1133[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 21:03:27 2026 +0330

    Update processed column filter/sort controls to use green design tokens consistently

[33mcommit 59bee5c74b6c0efac05c4808ef71bbd998050f61[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 20:58:23 2026 +0330

    Add linkedin_url extraction, per-tab dashboard refresh with timestamps, refactor analysis save/merge

[33mcommit f8c83a3cd66c0d4fa5a1db93d9e158f3937288fd[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 20:40:06 2026 +0330

    Add company_url to extraction/DB/drawer, update networking with company links, per-tab dashboard refresh buttons, move reprocess button next to rescore

[33mcommit b4444dbe2890329780a40f56a763468f25025a8a[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 20:17:50 2026 +0330

    Update gitignore: add db dir, exp-file.txt, untrack node_modules

[33mcommit 7a72ffcf0d7d4d3173a55cb9aecb5e342ba090e0[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 20:04:05 2026 +0330

    Remove legacy files: inputs/, jobs/, resumes/, stale DB, and temp files

[33mcommit a504257edda8b6a0ff2615dbdd0e14cdf70409e2[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 20:02:46 2026 +0330

    Add UI components, prompts, queue manager, and frontend updates

[33mcommit 20b4e9ec048ccc1f8dcb953e9d877066bedb998d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 20:00:21 2026 +0330

    Fix: rules wiped on every startup due to stale migration check (visa_sponsorship → visa_requirement)

[33mcommit 1145e5b0c33ae6150af9ac189e0b186197c66353[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 19:53:11 2026 +0330

    Fix DB_PATH resolution: always resolve relative paths against file directory, not CWD. Remove stale DB files.

[33mcommit da5c27b723e626ffd2bfa43c2bd1c8ea42737180[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 19:36:10 2026 +0330

    Rename preferences to rules across codebase for consistent naming

[33mcommit 32c0fd58f1926d8494beee2d920be8fddd043d68[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 19:12:23 2026 +0330

    Make scoring rules list draggable with auto priority adjustment

[33mcommit e9ad6c955d8bbd358c0aa9ef1251c9c1a229bf95[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 19:07:49 2026 +0330

    Add networking targets insight to dashboard, enlarge workflow step icons with tooltips

[33mcommit 9b29af2f35a8c9135fffefe673521659c1fc01cd[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 18:51:36 2026 +0330

    Remove resume placeholder from processing workflow, guard missing data dir, add python-dotenv to pyproject.toml

[33mcommit 1d7a82c8b3ac315f54dba1edb8fcb7a3f4ff1102[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 18:39:51 2026 +0330

    Move DB_PATH to .env, add tmp cleanup, remove inputs/ folder

[33mcommit 41085e65a1de4f8918130c44934fd2dd77a05f1d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 18:28:32 2026 +0330

    Auto-select latest resume/profile in list on tab load

[33mcommit 37f319a9024d64f81691c99a3856765f6178b929[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Sun Jul 19 12:45:57 2026 +0330

    feat: add adv_at, see_at, apply_reason fields to job records
    
    - Add adv_at (advertised at) with smart date estimation: '1 month' = 1mo ago, '1 month+' = 1.5mo, '4 months+' = 4.5mo; defaults to current time when no date info
    - Add see_at (seen at) timestamp for when the job was added to DB
    - Add apply_reason field generated by scoring AI: 1-2 sentence summary of why to apply or skip
    - Show adv_at/see_at timestamps on job cards and in drawer Details tab
    - Show apply_reason as a colored banner at top of job drawer (green=apply, yellow=consider, red=skip)
    - Update DB schema with migration support for existing databases
    - Update worker, stream_server, and scoring prompt for the new fields
    - Add adv_at and see_at to allowed sort fields in API

[33mcommit 6d811a319d4ecd09007bf42b47bc55871ee872cd[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 16 23:20:11 2026 +0330

    feat: add shadcn-compatible global.css tokens, update UI and server
    
    - Add global.css with oklch design tokens (light/dark themes)
    - Refactor App.jsx with improved UI components and layout
    - Update server prompts and worker for better job processing
    - Add package-lock.json updates

[33mcommit 97c20c486495b59510af7447ca7330fb58809510[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Thu Jul 16 16:15:18 2026 +0330

    feat: complete job processing overhaul with stop/pause/rescore/reprocess
    
    Backend:
    - Add stop (reset from scratch), pause (resume current step), reprocess (full pipeline) actions
    - Rescore now uses background flag without moving job to processing queue
    - Reprocess hard-deletes old job only after new processing succeeds
    - Add validate step (AI checks if URL is job description) and summary step
    - Rename prompts to step-ordered names (step2_validate, step4_extract, step7_score)
    - Move all temp files to system tempdir, remove data/ folder entirely
    - SQLite WAL mode + timeout for concurrent access between Flask and worker threads
    
    Frontend:
    - Combined Processing + Failed into single scrollable column
    - Custom confirm dialogs (no native window.confirm) for delete/rescore/reprocess
    - Duplicate URL dialog with Rescore/Reprocess choice (no second popup)
    - Job drawer: two-column header, fixed Open Job Page + Copy URL buttons
    - Action suggestion badge at top of drawer, iframe-isolated resume tab
    - Refresh/Rescore All/Reprocess All buttons with distinct icons
    - Server-side filtering and sorting for Processed column
    - Compact workflow steps pipeline with horizontal scroll
    - Toast notification for clipboard copy
    
    DB:
    - Migrate permanent data files to SQLite, remove data/*.json
    - Add rescoring, step_validate, step_summary columns to pending_jobs
    - load_json_to_db() no-op (data already in DB)

[33mcommit 3d46bf0795b6b3a31e9c269ab3e62def68ed23da[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 22:57:13 2026 +0330

    Auto-migrate DB schema on app start
    
    - Add _ensure_db_schema() to add missing columns automatically
    - Prevents column mismatch errors when columns are added

[33mcommit b459e126ca1f8bab8a0e9f9462d75b47205df317[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 22:52:38 2026 +0330

    Update jobs.db with structured_description column

[33mcommit edeee41cd11521ce71a06e06796c3de5e1461c02[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 22:51:44 2026 +0330

    Clean up jobs folder - keep only raw description files
    
    - Remove old duplicate files with smaller content
    - Keep backfill files with complete raw descriptions (47 files)

[33mcommit dbb4244a555f3c0f153ee308bff6287b80b9fe19[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 22:47:26 2026 +0330

    Add structured job description extraction
    
    - Add job_extract.txt prompt for extracting structured info from raw descriptions
    - Add structured_description column to jobs table
    - Worker now extracts structured info (requirements, responsibilities, benefits, etc.)
    - Update analysis_update.txt to use structured_description when available
    - Update job_processing.txt to note pre-extracted data availability
    - Add backfill_structured.py script for one-time migration

[33mcommit a962a9c7e45fd93aea829fd415cd12ff5e49a94d[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 22:42:01 2026 +0330

    Store raw job descriptions in DB and jobs/ folder
    
    - Add raw_description column to jobs table
    - Worker now saves raw fetched content to DB and jobs/ folder
    - Backfill script fetches missing raw descriptions from web
    - Includes 2-4s delay between fetches to avoid rate limiting
    - All 48 existing jobs backfilled with raw descriptions

[33mcommit 23e342b02223c2c3753a0372a342ce4e7a1ff422[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 22:22:13 2026 +0330

    Migrate analysis to SQLite, merge Dashboard+Skills, remove metadata
    
    - Add analysis_runs table for flexible JSON-based analysis storage
    - Create unified analysis API (GET /api/analysis, POST /api/refresh/analysis)
    - Merge Dashboard and Skills into single tab with inner tabs (Overview/Strategy/Skills)
    - Add new sections: Skill-Job Fit Analysis, Learning ROI
    - Remove /api/metadata endpoint (analysis.created_at replaces it)
    - Remove old dashboard_insights_*.json and pending_result_*.json files
    - Update worker to save analysis to analysis_runs table
    - Add analysis_update.txt prompt for unified analysis generation

[33mcommit 1d65b3408203c8ecdf3e71b0167980f14d11de8b[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 21:24:51 2026 +0330

    Fix dropdown positioning for rightmost filter
    
    - Add alignRight prop to MultiSelect component
    - Employment type filter (rightmost) now opens dropdown to the left
    - Prevents dropdown from overflowing column border

[33mcommit ab3f4e40becfe9b9b34df7beaa1445a41b9530ac[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 21:19:49 2026 +0330

    Add last update timestamps and improve filter layout
    
    - Add metadata table for storing last update timestamps
    - Add API endpoints for metadata (GET/PUT)
    - Dashboard and Skills tabs show last updated time
    - Move search box to first row (full width)
    - Move sort into dropdown on second row left
    - Filters on second row right
    - Default sort changed to newest (created_at desc)
    - Sort dropdown with direction toggle button

[33mcommit b54b12a36b0296b6fe762d5c7265e6488ecb12af[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 21:09:24 2026 +0330

    Add employment type, work_types columns and fix filters
    
    - Add employment_type column (Full-time, Part-time, Contract, Internship, Temporary)
    - Add work_types column (JSON array for multiple work arrangements)
    - Update prompt to extract employment type and multiple work types
    - Add employment type filter to processed jobs
    - Fix MultiSelect component sizing (smaller, no overflow)
    - Fix filter layout with flex-wrap
    - Update normalization logic for new fields
    - Update .gitignore to exclude node_modules and build files

[33mcommit 1ea48fe106c6abba5c1ee7ac041c00011fbc9bf6[m
Author: Hassan Mohagheghian <hassan.mohagheghian.cs@gmail.com>
Date:   Wed Jul 15 21:01:18 2026 +0330

    Initial commit: Job Search dashboard with AI-powered analysis
    
    - Flask backend with job processing workflow
    - React frontend with Kanban board and dashboard
    - AI-powered job scoring and resume tailoring
    - Multi-location support with normalized city data
    - Dashboard insights with manual refresh
    - Skills tracking with tech stack analysis
    - Preferences system for scoring criteria
    - Soft delete with re-queue capability
    - WebSocket streaming for real-time updates
