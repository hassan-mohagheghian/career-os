# AI Agent Architecture

## Overview

The AI Agent Orchestration Layer provides a flexible, multi-provider agent system that wraps the existing Mimo CLI integration. It introduces:

- **Provider Abstraction**: Swap LLM providers without changing agent code
- **Agent Runtime**: LangGraph-based workflow orchestration with state management
- **Tool System**: Domain services wrapping existing business logic
- **Workflow Graphs**: Composable, stateful processing pipelines

```
React SPA
    │
Flask API
    │
Application Services
    │
AI Agent Layer
    │
Agent Runtime (LangGraph)
    │
LLM Provider Layer
    │
┌─────────────────────────────────────────┐
│  MimoProvider  │  OpenAI  │  Local LLM  │
└─────────────────────────────────────────┘
```

## Directory Structure

```
app/ai/
├── __init__.py
├── logging.py                    # Structured agent events
├── providers/
│   ├── __init__.py               # Factory + registry
│   ├── base.py                   # LLMProvider ABC
│   ├── mimo/adapter.py           # MimoProvider (wraps MimoRunner)
│   ├── openai/adapter.py         # OpenAIProvider (stub)
│   └── local/adapter.py          # LocalLLMProvider (stub)
├── agents/
│   ├── runtime/
│   │   ├── state.py              # AgentState TypedDict
│   │   ├── graph.py              # GraphBuilder (LangGraph wrapper)
│   │   ├── executor.py           # AgentExecutor (node runner)
│   │   └── registry.py           # AgentRegistry (singleton)
│   ├── job/
│   │   ├── extractor.py          # JobExtractorAgent
│   │   ├── analyzer.py           # JobAnalyzerAgent
│   │   ├── scorer.py             # JobScorerAgent
│   │   └── graph.py              # JobProcessingGraph
│   ├── company/
│   │   ├── researcher.py         # CompanyResearcherAgent
│   │   ├── evaluator.py          # CompanyEvaluatorAgent
│   │   └── graph.py              # CompanyProcessingGraph
│   ├── skills/intelligence.py    # SkillIntelligenceAgent
│   ├── resume/generator.py       # ResumeAgent
│   └── insights/
│       ├── generator.py          # InsightsAgent
│       └── graph.py              # InsightsGenerationGraph
├── tools/
│   ├── base.py                   # BaseTool ABC + ToolResult
│   ├── database.py               # DatabaseTool (read-only SQL)
│   ├── job_tools.py              # FetchJobTool, ExtractJobDataTool
│   ├── company_tools.py          # FetchCompanyTool, AnalyzeCompanyTool
│   ├── skill_tools.py            # FindSkillTool, CalculateSkillGapTool
│   └── resume_tools.py           # GenerateResumeSectionTool
└── prompts/
    └── registry.py               # PromptRegistry
```

## Provider System

### Adding a New Provider

1. Create `app/ai/providers/<name>/adapter.py`
2. Implement `LLMProvider` interface:

```python
from app.ai.providers.base import LLMProvider, ProviderConfig, ProviderResponse

class MyProvider(LLMProvider):
    def generate(self, prompt, context=None, timeout=None):
        # Call your LLM here
        return ProviderResponse(content="response", provider="my_provider")

    def generate_structured(self, prompt, schema=None, context=None, timeout=None):
        # Return JSON-structured response
        return ProviderResponse(content='{"key": "value"}', provider="my_provider")
```

3. Register in `app/ai/providers/__init__.py`:

```python
def _create_provider(name, config):
    if name == "my_provider":
        from .my_provider.adapter import MyProvider
        return MyProvider(config)
```

4. Set `AI_PROVIDER=my_provider` in `.env`

### Provider Interface

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt, context=None, timeout=None) -> ProviderResponse: ...
    @abstractmethod
    def generate_structured(self, prompt, schema=None, context=None, timeout=None) -> ProviderResponse: ...
    def close(self): ...  # Optional cleanup
    def as_langchain_llm(self) -> BaseChatModel: ...  # Optional LangChain bridge
```

## Agent System

### Adding a New Agent

1. Create `app/ai/agents/<domain>/<name>.py`
2. Implement agent class with `execute()` method:

```python
from app.ai.agents.runtime.state import AgentState, create_initial_state
from app.ai.agents.runtime.executor import AgentExecutor

class MyAgent:
    def __init__(self, provider=None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state=None):
        if state is None:
            state = create_initial_state()
        nodes = [("step1", self._step1), ("step2", self._step2)]
        return self._executor.execute_chain(nodes, state)

    def _step1(self, state):
        state["output"] = "processed"
        return state

    def _step2(self, state):
        return state
```

3. Register in `AgentRegistry`:

```python
from app.ai.agents.runtime.registry import AgentRegistry
registry = AgentRegistry.instance()
registry.register("my_agent", MyAgent(), description="Does something")
```

### Agent Design Principles

- **Thin orchestration**: Agents coordinate, they don't implement business logic
- **Tool delegation**: Business operations happen via tools
- **State passing**: All context flows through `AgentState` dict
- **Error isolation**: One node failing doesn't crash the whole agent

## Workflow Graphs

### Building a Graph

```python
from app.ai.agents.runtime.graph import GraphBuilder

builder = GraphBuilder("my_workflow")
builder.add_node("fetch", fetch_fn)
builder.add_node("process", process_fn)
builder.add_node("save", save_fn)
builder.add_edge("fetch", "process")
builder.add_edge("process", "save")
builder.set_entry("fetch")
builder.set_finish("save")

graph = builder.compile()
result = graph.invoke(initial_state)
```

### Graph Features

- **Sequential edges**: `add_edge("a", "b")` — A runs, then B
- **Conditional edges**: `add_conditional_edge("a", router_fn, {"yes": "b", "no": "c"})`
- **Error handling**: Nodes that fail are recorded in `state["errors"]`
- **Node history**: Every executed node is logged in `state["node_history"]`

### Built-in Graphs

| Graph | Flow | Use Case |
|-------|------|----------|
| `JobProcessingGraph` | fetch → validate → extract → score | Job analysis pipeline |
| `CompanyProcessingGraph` | fetch → extract → analyze → save | Company intelligence |
| `InsightsGenerationGraph` | overview → opportunities → companies → market → networking → skills_intel | Career insights |

## Tool System

### Adding a New Tool

```python
from app.ai.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def name(self):
        return "my_tool"

    @property
    def description(self):
        return "Does something useful"

    def run(self, **kwargs):
        # Implement tool logic
        return ToolResult(success=True, data={"result": "ok"})
```

### Existing Tools

| Tool | Wraps | Purpose |
|------|-------|---------|
| `FetchJobTool` | `worker._fetch_url()` | Fetch job posting content |
| `ExtractJobDataTool` | `worker._extract_all()` | Extract structured job data |
| `ScoreJobTool` | `worker.normalize_score()` | Score job fit |
| `FetchCompanyTool` | `company_worker._fetch_url()` | Fetch company content |
| `ExtractCompanyTool` | `company_worker._extract_company_info()` | Extract company data |
| `AnalyzeCompanyTool` | `company_worker._analyze_company()` | Generate company intelligence |
| `FindSkillTool` | DB query | Find skill by name |
| `CalculateSkillGapTool` | Pure logic | Compare required vs user skills |
| `DatabaseTool` | Raw SQL | Read-only DB queries |
| `GenerateResumeSectionTool` | DB query | Load resume for tailoring |

## Configuration

### Environment Variables

```bash
AI_PROVIDER=mimo          # Provider selection: mimo, openai, local
TEMP_DIR=tmp              # Temporary files directory
QUEUE_CONCURRENCY=2       # Max parallel processing jobs
DB_PATH=db/jobs.db        # Database path
```

### Dynamic Provider Selection

The provider is selected at startup based on `AI_PROVIDER`. Agents never call `MimoRunner` directly — they go through the provider abstraction.

## Logging

Agent events use structured logging via `structlog`:

```python
from app.ai.logging import agent_started, agent_completed, provider_called

agent_started("job_analyzer", provider="mimo")
provider_called("mimo", "mimo-cli", duration=1.5)
agent_completed("job_analyzer", duration=12.4, provider="mimo")
```

Events: `agent_started`, `agent_completed`, `agent_failed`, `provider_called`, `workflow_finished`

## Testing

```bash
# Run AI layer tests
uv run pytest tests/test_ai/ -v

# Run all tests
uv run pytest tests/test_ai/ app/server/tests/ -v
```

### Test Structure

```
tests/test_ai/
├── conftest.py          # Shared fixtures (mock provider, test DB)
├── test_providers.py    # Provider interface, factory, MimoProvider
├── test_agents.py       # State, registry, executor
├── test_tools.py        # Tool interface, job/company/skill tools
└── test_workflows.py    # Graph builder, compiled graphs, integration
```

## Design Principles

- **DDD**: Bounded contexts (Provider, Agent, Tool, Workflow), value objects, entities
- **SOLID**: Each class has one responsibility, depends on abstractions
- **TDD**: Tests define contracts, implementation follows
- **OOP**: Inheritance for providers, composition for agents
- **Design Patterns**: Factory, Strategy, Registry, Builder, Observer, Command
- **No business logic in agents**: Agents orchestrate; services implement
- **Backward compatible**: Existing workers continue to work unchanged
