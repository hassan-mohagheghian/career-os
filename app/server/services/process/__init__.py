"""
Processing pipeline — domain models, infrastructure, and workers.

Architecture:
  models.py       → Domain value objects and entities (DDD)
  interfaces.py   → Abstract base classes — contracts (SOLID: Dependency Inversion)
  repository.py   → SQLite repositories (DDD: Repository pattern)
  process_manager.py → Subprocess lifecycle with process groups
  temp_manager.py → Temp file tracking and cleanup
  mimo_runner.py  → mimo CLI invocation (Strategy pattern)
  broadcaster.py  → Real-time status delivery (Observer pattern)
  worker_base.py  → Abstract worker pipeline (Template Method pattern)
  job_worker.py   → Job processing implementation
  company_worker.py → Company processing implementation
"""
