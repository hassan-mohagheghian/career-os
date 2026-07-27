"""
Processing pipeline — domain models, infrastructure, and workers.

Architecture:
  models.py            → Domain value objects and entities (DDD)
  generation_models.py → Unified generation types (DDD)
  interfaces.py        → Abstract base classes — contracts (SOLID: Dependency Inversion)
  repository.py        → SQLite repositories (DDD: Repository pattern)
  generation_repository.py → Unified generation history repository
  process_manager.py   → Subprocess lifecycle with process groups
  temp_manager.py      → Temp file tracking and cleanup
  mimo_runner.py       → mimo CLI invocation (Strategy pattern)
  broadcaster.py       → Real-time status delivery (Observer pattern)
  worker_base.py       → Abstract worker pipeline (Template Method pattern)
  job_worker.py        → Job processing implementation
  company_worker.py    → Company processing implementation
  generation_worker.py → Resume/cover letter generation implementation
  insights_service.py  → Career intelligence service (OOP wrapper)
  skill_roadmap_service.py → Skill roadmap service (OOP wrapper)
"""
