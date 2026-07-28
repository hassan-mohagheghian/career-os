# Provider Capabilities Matrix

## Current Providers

| Provider | Status | Native Tools | Streaming | Structured Output |
|----------|--------|-------------|-----------|-------------------|
| Mimo CLI | Active | CLI subprocess | ✅ | Via result files |
| OpenCode | Active | CLI subprocess | ✅ | Via result files |
| Agy | Active | CLI subprocess | ✅ | Via result files |
| Gemini | Implemented | API native | ✅ | `with_structured_output()` |
| OpenAI | Stub | API native | ❌ | ❌ |
| Local | Stub | N/A | ❌ | ❌ |

## Tool Usage Analysis

### Current State

The codebase currently does NOT use provider-native tool calling. All LLM interactions are:

1. **Prompt-based**: Prompts are sent as text, results parsed from files
2. **Subprocess-based**: Mimo/OpenCode/Agy spawn CLI processes
3. **API-based**: Gemini uses LangChain's ChatModel

### Provider-Specific Considerations

#### OpenAI

| Feature | Available | Recommended | Reason |
|---------|-----------|-------------|--------|
| Web Browsing | ✅ | ❌ | Slower and more expensive than local fetch |
| Code Interpreter | ✅ | ❌ | Can execute Python locally instead |
| File Search | ✅ | ❌ | Can search local files |
| Function Calling | ✅ | ⚠️ | Only for complex analysis |

#### Anthropic

| Feature | Available | Recommended | Reason |
|---------|-----------|-------------|--------|
| Web Search | ✅ | ❌ | Local fetch is faster |
| Computer Use | ✅ | ❌ | Overkill for text extraction |

#### Gemini

| Feature | Available | Recommended | Reason |
|---------|-----------|-------------|--------|
| Google Search | ✅ | ❌ | Local fetch for known URLs |
| Code Execution | ✅ | ❌ | Can run Python locally |
| Grounding | ✅ | ⚠️ | Useful for fact-checking |

## Recommendation

**For this project**: Never use provider-native tools for:

- URL fetching
- HTML parsing
- Content extraction
- File reading
- Database queries
- Code execution

**Consider provider-native tools for**:

- Complex reasoning tasks
- Multi-step analysis requiring tool chains
- Tasks that benefit from provider-specific capabilities (e.g., grounding)

## Future Provider Support

When adding new providers:

1. Evaluate native tools against local alternatives
2. Document cost/latency trade-offs
3. Default to local tools unless provider offers measurable benefit
4. Use the Tool Registry's priority system to select the best tool
