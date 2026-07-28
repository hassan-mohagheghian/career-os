You are working on the existing "Job Search Intelligence" project.

Your task is to introduce an AI Agent Orchestration Layer using modern production-grade agent frameworks without breaking the current architecture.

The goal is to evolve the current AI architecture from a single Mimo CLI subprocess integration into a flexible multi-provider agent system that can support Mimo CLI now and future providers such as OpenAI API, Anthropic, Ollama/local LLMs, and other CLI/API-based LLM providers.

IMPORTANT:
- Do not rewrite existing business logic.
- Do not move existing feature boundaries.
- Preserve the current Flask + React architecture.
- Preserve raw SQL database approach.
- Do not add ORM.
- Keep backward compatibility with current Mimo workflows.
- Follow existing project coding rules.

==================================================
CURRENT ARCHITECTURE CONTEXT
==================================================

Current flow:

React SPA
    |
Flask API
    |
Service Layer
    |
MimoRunner
    |
Mimo CLI subprocess
    |
LLM


Target architecture:

React SPA
    |
Flask API
    |
Application Services
    |
AI Agent Layer
    |
Agent Runtime
    |
LLM Provider Layer
    |
--------------------------------
Mimo CLI Adapter
OpenAI Adapter
Local LLM Adapter
Future Providers
--------------------------------


==================================================
MAIN OBJECTIVES
==================================================

Implement a new AI layer with:

1. Agent orchestration
2. Provider abstraction
3. Tool system
4. Workflow graphs
5. Stateful execution
6. Future multi-agent support


Use:

- LangGraph as the primary workflow orchestration framework.
- LangChain components where useful for tools, prompts, and agent utilities.
- Keep the design open for LlamaIndex/RAG integration later.


==================================================
NEW ARCHITECTURE
==================================================

Create a new structure:

app/

├── ai/
│
├── agents/
│   │
│   ├── runtime/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── executor.py
│   │   └── registry.py
│   │
│   ├── job/
│   │   ├── extractor.py
│   │   ├── analyzer.py
│   │   └── scorer.py
│   │
│   ├── company/
│   │   ├── researcher.py
│   │   └── evaluator.py
│   │
│   ├── skills/
│   │   └── intelligence.py
│   │
│   ├── resume/
│   │   └── generator.py
│   │
│   └── insights/
│       └── generator.py
│
├── providers/
│
│   ├── base.py
│   ├── mimo/
│   │   └── adapter.py
│   │
│   ├── openai/
│   │   └── adapter.py
│   │
│   └── local/
│       └── adapter.py
│
├── tools/
│
│   ├── database.py
│   ├── job_tools.py
│   ├── company_tools.py
│   ├── skill_tools.py
│   └── resume_tools.py
│
└── prompts/
    └── registry.py


==================================================
LLM PROVIDER ABSTRACTION
==================================================

Create a provider interface.

Example:

class LLMProvider:

    def generate(
        self,
        prompt: str,
        context: dict | None = None
    ) -> str:
        raise NotImplementedError


Implement:

1. MimoProvider

Responsibilities:
- Wrap current MimoRunner functionality.
- Keep subprocess handling.
- Keep streaming/session support.


2. Future provider placeholders:

OpenAIProvider
LocalLLMProvider


They do not need full implementation yet, but architecture must support them.


Agents must never directly call MimoRunner.

They should only communicate through LLMProvider.


==================================================
LANGGRAPH IMPLEMENTATION
==================================================

Introduce LangGraph workflow support.

Create:

- Graph state definitions
- Node execution model
- Agent registry


Example:

JobProcessingGraph:

START

    |
    v

Job Extraction Agent

    |
    v

Skill Extraction Agent

    |
    v

Scoring Agent

    |
    v

Database Save

    |
    v

END


The graph should support:

- state passing
- retries
- future checkpoints
- future human approval steps


==================================================
INITIAL AGENTS
==================================================

Create initial agent interfaces for:


1. Job Analysis Agent

Responsibilities:
- Extract job information
- Analyze stack
- Identify skills
- Prepare structured output


2. Company Intelligence Agent

Responsibilities:
- Analyze company information
- Evaluate company profile
- Prepare visa/company intelligence data


3. Skill Intelligence Agent

Responsibilities:
- Analyze required skills
- Compare user skills
- Generate skill insights


4. Resume Agent

Responsibilities:
- Generate resume improvement suggestions
- Generate tailored content


5. Insights Agent

Responsibilities:
- Generate career intelligence sections


Agents should be thin orchestration layers.
Business rules remain inside existing services.


==================================================
TOOLS SYSTEM
==================================================

Introduce agent tools.

Examples:

Job tools:

- get_job()
- update_job()
- extract_job_data()


Company tools:

- get_company()
- analyze_company()


Skill tools:

- find_skill()
- merge_skill_alias()
- calculate_skill_gap()


Resume tools:

- generate_resume_section()


Tools should wrap existing services instead of duplicating logic.


==================================================
PROMPT MANAGEMENT
==================================================

Create a centralized prompt registry.

Current prompts exist in:

- insights/
- skill_roadmaps/
- job_processing/
- company/


Do not duplicate prompts.

Move toward:

prompts/

├── jobs/
├── companies/
├── skills/
├── resume/
└── insights/


Support:

- versioning
- reusable templates
- agent-specific prompts


==================================================
CONFIGURATION
==================================================

Add configuration:

AI_PROVIDER=mimo


Future:

AI_PROVIDER=openai
AI_PROVIDER=local


The application should select provider dynamically.


==================================================
LOGGING
==================================================

Use existing:

structlog


Add structured events:

agent_started
agent_completed
agent_failed
provider_called
workflow_finished


Example:

{
 "agent": "job_analyzer",
 "provider": "mimo",
 "duration": 12.4,
 "status": "success"
}


==================================================
DATABASE
==================================================

Do not introduce migrations unless required.

Do not change existing tables.

If agent execution tracking is needed, propose a migration first.

==================================================
TESTING
==================================================

Add tests for:

- Provider interface
- Mimo adapter
- Agent execution
- LangGraph workflow
- Tool execution


Follow existing pytest structure.


==================================================
DELIVERABLES
==================================================

Implement incrementally:

Phase 1:
- Provider abstraction
- Mimo adapter migration
- LangGraph base runtime


Phase 2:
- Convert current job processing workflow into LangGraph


Phase 3:
- Add company, skills, resume, insights agents


Phase 4:
- Add future provider support


At the end create/update documentation:

docs/AI_ARCHITECTURE.md

The document must explain:

- Agent architecture
- Workflow diagrams
- Provider system
- How to add new agents
- How to add new LLM providers
- How future developers or AI coding agents can understand and extend this system


The final result should transform the project into a production-ready AI agent architecture while preserving the existing application.
