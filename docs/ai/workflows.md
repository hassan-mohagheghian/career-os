# AI Workflow Graphs

## Overview

All AI generation workflows are implemented as LangGraph-based state machines. Each graph is a self-contained pipeline that owns its prompts, returns typed Pydantic models, and supports retry, checkpointing, and streaming.

## Architecture

```
graphs/
├── runtime/                    # Core graph infrastructure
│   ├── state.py               # BaseState TypedDict + Pydantic output models
│   ├── graph.py               # GraphBuilder + CompiledGraph
│   ├── executor.py            # AgentExecutor with retry support
│   └── registry.py            # AgentRegistry for discovery
├── job/                        # Job processing workflows
│   ├── graph.py               # Job processing pipeline
│   ├── extractor.py           # Job extraction agent
│   ├── analyzer.py            # Job analysis agent
│   └── scorer.py              # Job scoring agent
├── company/                    # Company intelligence workflows
│   ├── graph.py               # Company processing pipeline
│   ├── researcher.py          # Company research agent
│   └── evaluator.py           # Company evaluation agent
├── resume/                     # Resume generation workflows
│   ├── generator.py           # Resume generation pipeline
│   └── cover_letter.py        # Cover letter generation pipeline
├── skills/                     # Skill management workflows
│   ├── extraction.py          # Skill extraction pipeline
│   ├── roadmap.py             # Skill roadmap generation
│   └── intelligence.py        # Skill intelligence agent
├── insights/                   # Career insights workflows
│   ├── graph.py               # All insight graphs (6 children + parent)
│   └── generator.py           # Insights generation agent
└── generate_all.py            # Parent orchestrator graph
```

## Available Graphs

| Graph Name | Description | Entry Point |
|------------|-------------|-------------|
| `job_processing` | Job posting analysis pipeline | `validate_input` |
| `company_processing` | Company intelligence pipeline | `validate_input` |
| `resume_generation` | Tailored resume creation | `load_resume` |
| `cover_letter_generation` | Cover letter creation | `load_resume` |
| `skill_extraction` | Skill extraction from jobs | `load_jobs` |
| `skill_roadmap` | Learning roadmap generation | `load_current_skills` |
| `insights` | Career intelligence (6 sections) | `overview` |
| `generate_all` | Parent orchestrator | `job_processing` |

## Usage

```python
from ai.infrastructure.graphs import get_graph, get_all_graphs

# Get a specific graph
graph = get_graph("job_processing")
compiled = graph.compile()
result = compiled.invoke(create_initial_state(input="https://..."))

# Get all graphs
graphs = get_all_graphs()
for name, builder in graphs.items():
    compiled = builder.compile()
    # ...
```

## State Flow

Each graph uses `BaseState` (TypedDict) flowing through nodes:

```python
BaseState = {
    "input": str,           # User input
    "output": str,          # Final output (JSON)
    "context": dict,        # Shared context (provider, config)
    "errors": list[str],    # Error messages
    "metadata": dict,       # Intermediate data
    "node_history": list,   # Executed node names
}
```

## Typed Outputs

Every graph returns strongly typed Pydantic models:

- `JobExtractionOutput` / `JobAnalysisOutput`
- `CompanyExtractionOutput` / `CompanyAnalysisOutput`
- `ResumeOutput`
- `CoverLetterOutput`
- `SkillExtractionOutput`
- `SkillRoadmapOutput`
- `InsightSectionOutput` / `CareerInsightsOutput`

## Common Features

- **Retry**: Configurable per-node with `builder.set_retry("node", max_retries=3)`
- **Checkpoint**: Via LangGraph's `MemorySaver`
- **Streaming**: Via `compiled.stream(state)`
- **Error Recovery**: Partial failure support in insights graph
- **Provider Abstraction**: All LLM calls through `LLMProvider` interface
