# Prompt Versioning

## Version Strategy

Every prompt has a semantic version string (e.g. `1.0.0`). The registry supports multiple versions of the same prompt identifier.

- **Latest version** is the highest version string (sorted lexicographically).
- Workflows request prompts by identifier; the registry resolves the version.
- Old versions remain accessible for regression testing and rollback.

## Creating a new version

```python
from ai.infrastructure.prompts import get_registry

registry = get_registry()
registry.create_version(
    identifier="job.extract",
    template="Improved template with {content}",
    version="2.0.0",
    description="Added structured output schema validation",
)
```

## Version metadata

Each `PromptSpec` includes:
- `version` — Semantic version string
- `changelog` — List of `PromptVersion(version, description, date)` entries
- `description` — What changed in this version

## Example

```python
registry = get_registry()

# Default: latest version
v2 = registry.get("job.extract")
assert v2.version == "2.0.0"

# Specific version
v1 = registry.get("job.extract", version="1.0.0")
assert v1.version == "1.0.0"
```
