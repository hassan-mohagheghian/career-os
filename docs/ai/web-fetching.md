# Web Fetching

## Overview

The unified web fetcher replaces all duplicated `_fetch_url` functions across the codebase with a single, configurable implementation.

## Pipeline

```
URL Input
    │
    ▼
HTTP Request (with custom headers, timeout)
    │
    ▼
Redirect Handling (automatic)
    │
    ▼
Retry Logic (configurable, exponential backoff)
    │
    ▼
Encoding Detection (UTF-8 with fallback)
    │
    ▼
HTML Cleaning
    ├── Strip <script> tags
    ├── Strip <style> tags
    ├── Strip HTML comments
    ├── Remove HTML tags
    ├── Decode HTML entities
    └── Normalize whitespace
    │
    ▼
Main Content Extraction
    ├── Find content markers (e.g., "About The Role")
    ├── Extract text after marker
    └── Fallback to full cleaned text
    │
    ▼
Length Validation
    ├── Minimum: 100 chars (error if shorter)
    └── Maximum: Configurable (default 5000)
    │
    ▼
Structured Result (FetchedPage)
```

## API

### `fetch_page(url, **kwargs)`

```python
from ai.infrastructure.tools.fetch import fetch_page

page = fetch_page(
    url="https://example.com/job/123",
    timeout=30,          # Request timeout
    max_retries=2,       # Retry attempts
    max_length=5000,     # Max text length
    content_markers=[    # Markers for main content
        "About The Role",
        "Job Description",
    ],
    strip_scripts=True,  # Remove <script> tags
    extract_main=True,   # Attempt main content extraction
)

if page.is_ok:
    print(page.plain_text)      # Cleaned text
    print(page.status_code)     # HTTP status
    print(page.cache_hit)       # Was it cached?
    print(page.language)        # Detected language
else:
    print(page.error.code)      # Error code
    print(page.error.message)   # Human-readable error
```

### `extract_content(html, **kwargs)`

Lower-level function for HTML extraction:

```python
from ai.infrastructure.tools.fetch import extract_content

result = extract_content(
    html="<html><body>...</body></html>",
    strip_scripts=True,
    extract_main=True,
    content_markers=["Job Description"],
)

print(result.cleaned_text)    # Cleaned text
print(result.main_content)    # Main content section
print(result.word_count)      # Word count
print(result.language)        # Detected language
```

## Error Handling

| Error Code | Description | Retryable |
|------------|-------------|-----------|
| `INVALID_URL` | URL is malformed | No |
| `NOT_FOUND` | 404 error | No |
| `ACCESS_DENIED` | 403 error | No |
| `RATE_LIMITED` | 429 error | Yes |
| `SERVICE_UNAVAILABLE` | 503 error | Yes |
| `NETWORK_ERROR` | Connection failed | Yes |
| `CONTENT_TOO_SHORT` | Content < 100 chars | No |
| `FETCH_ERROR` | Unexpected error | Yes |

## Caching

Web fetching integrates with the content cache:

```python
from ai.infrastructure.tools.web import WebFetchTool

tool = WebFetchTool(
    use_cache=True,      # Enable caching
    ttl_seconds=21600,   # 6 hour TTL
)

# First fetch: HTTP request + cache write
result1 = tool.run(url="https://example.com")

# Second fetch: Cache hit (no HTTP request)
result2 = tool.run(url="https://example.com")
assert result2.metadata["cache_hit"] is True
```

## Migration from Old Code

Before (duplicated across 4 files):

```python
def _fetch_url(url):
    req = urllib.request.Request(url, headers={...})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:5000]
```

After (single implementation):

```python
from ai.infrastructure.tools.fetch import fetch_page

def _fetch_url(url):
    page = fetch_page(url)
    if page.is_ok:
        return page.plain_text
    raise RuntimeError(page.error.message)
```
