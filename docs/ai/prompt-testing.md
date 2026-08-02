# Prompt Testing

## Test Categories

Every prompt should have tests verifying:

1. **Rendering** — The prompt renders without errors with valid inputs
2. **Variables** — All template variables are correctly substituted
3. **Missing inputs** — Missing optional variables don't cause errors
4. **Structured output** — The prompt instructs the LLM to return structured output
5. **Regression** — Changes don't break existing behavior
6. **Golden output** — Known inputs produce expected output patterns

## Running tests

```bash
pytest apps/backend/tests/ai/infrastructure/prompts/ -v
```

## Test structure

Tests are in `apps/backend/tests/ai/infrastructure/prompts/test_prompt_platform.py`:

- `TestPromptRegistry` — Registry operations (register, get, list, versioning)
- `TestPromptRendering` — Each prompt renders correctly with typical inputs
- `TestTypedInputModels` — Pydantic input models work end-to-end
- `TestPromptRenderingEdgeCases` — Empty variables, special chars, unicode, large content
- `TestPromptTypeEnum` — All prompt types are defined
- `TestPromptObservability` — Logger tracks renders and execution
- `TestPromptSpec` — PromptSpec creation and defaults
- `TestPromptTemplateConstruction` — `from_string`, `from_messages`, etc.
- `TestReusableComponents` — Tone, formatting, JSON rules
- `TestGoldenOutput` — Known inputs produce expected patterns
- `TestPromptTemplatePartialVars` — Partial variable handling

## Writing new prompt tests

```python
def test_my_prompt_renders(get_prompt):
    result = get_prompt("my.prompt", var1="value1", var2="value2")
    assert "expected content" in result

def test_my_prompt_missing_vars(get_prompt):
    result = get_prompt("my.prompt")  # Missing vars get empty string defaults
    assert result is not None
```
