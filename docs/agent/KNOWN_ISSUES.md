# Known Issues

- **Career Intelligence concurrency**: Only one analysis can run at a time. If triggered while running, returns HTTP 409.
- **Mimo CLI timeout**: Analysis prompts have 300s timeout. Complex analyses may exceed this.
- **Single-user**: No multi-tenant support. SQLite is single-file.
- **WebSocket flakiness**: Can disconnect on slow networks during job processing.
- **Frontend bundle size**: ~820KB minified. Consider code splitting for optimization.
