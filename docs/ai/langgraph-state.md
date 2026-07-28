# LangGraph State Design

## BaseState

Every workflow state extends `BaseState` (TypedDict):

```python
class BaseState(TypedDict, total=False):
    input: str
    output: str
    context: dict[str, Any]
    errors: list[str]
    metadata: dict[str, Any]
    node_history: list[str]
```

## Workflow-Specific States

Each workflow adds typed fields specific to its domain. States are defined in `runtime/state.py`.

### JobProcessingState

```python
class JobProcessingState(BaseState):
    raw_content: str
    job_title: str
    job_company: str
    job_num: int
    fit_score: Optional[float]
    success_score: Optional[float]
    extraction_data: dict[str, Any]
    resume_text: str
    linkedin_text: str
    rules: str
```

### CompanyProcessingState

```python
class CompanyProcessingState(BaseState):
    raw_content: str
    company_name: str
    company_type: str
    extraction_data: dict[str, Any]
    intelligence_data: dict[str, Any]
    scores: dict[str, Any]
    company_id: Optional[int]
```

## Node Communication

Nodes follow a strict pattern:

1. Read from `state` dict (strongly typed fields)
2. Call the LLM service (if needed)
3. Write results back to `state` dict
4. Return the updated `state`

Never write to files, never read from files.
