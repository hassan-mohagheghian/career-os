# AI Bounded Context Architecture

## Overview

The AI bounded context is responsible for all AI/ML processing in the platform. It owns:

- **Providers**: LLM provider abstraction and management
- **Prompts**: Prompt templates per graph node
- **Graphs**: LangGraph workflow definitions
- **Tools**: Reusable LangChain tools
- **Parsers**: Structured output parsing with Pydantic
- **Execution Engine**: Graph execution with progress tracking

## Architecture

```
ai/
├── domain/
│   ├── entities/
│   │   └── generation_session.py      # Tracks workflow executions
│   ├── value_objects/
│   │   ├── graph_state.py             # State flowing through graphs
│   │   ├── provider_config.py         # Provider configuration
│   │   └── provider_response.py       # Standardized provider responses
│   └── repositories/
│       └── generation_session_repository.py  # Repository interface
├── application/
│   ├── commands/
│   │   └── process_job.py             # Command to process a job
│   ├── dto/
│   │   └── job_processing_result.py   # Result DTO
│   └── use_cases/
│       └── process_job.py             # Use case orchestration
├── infrastructure/
│   ├── models/
│   │   └── generation_session_model.py  # SQLAlchemy model
│   ├── repositories/
│   │   └── generation_session_repository.py  # Repository implementation
│   ├── providers/
│   │   ├── base.py                    # Abstract provider interface
│   │   └── factory.py                 # Provider factory
│   ├── graphs/
│   │   ├── executor.py                # Graph execution engine
│   │   └── job_processing.py          # Job processing graph (12 stages)
│   ├── tools/
│   │   ├── base.py                    # Abstract tool interface
│   │   └── job_tools.py               # Job-related tools
│   ├── prompts/
│   │   ├── manager.py                 # Prompt management
│   │   └── jobs/                      # Job-specific prompts
│   ├── parsers.py                     # Structured output parsers
│   ├── progress.py                    # Progress event emitter
│   └── error_handling.py              # Error handling strategies
└── presentation/
    └── (API endpoints for AI context)
```

## Design Principles

1. **DDD Bounded Context**: AI is a self-contained context with clear boundaries
2. **Dependency Inversion**: Business code depends on abstractions, not implementations
3. **Single Responsibility**: Each component has one clear purpose
4. **Open/Closed**: New providers, tools, and graphs can be added without modifying existing code

## Graph Execution

Every business workflow becomes a graph. The job processing graph has 12 stages:

1. Input Validation
2. URL Fetching
3. Fallback to Notes
4. Raw Content Extraction
5. Content Cleaning
6. Structured Extraction
7. Job Analysis
8. Skill Extraction
9. Scoring (Fit Score, Success Score)
10. Summary Generation
11. Persistence
12. Completion Event

## Provider Architecture

Business code never depends on provider SDKs. Providers are replaceable through configuration:

- OpenAI
- OpenRouter
- Anthropic
- Google Gemini
- Local models

## Error Handling

- **Retry Strategy**: Exponential backoff for transient failures
- **Fallback Strategy**: Provider failover on critical failures
- **Graceful Degradation**: Partial results when possible
