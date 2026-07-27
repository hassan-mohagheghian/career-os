# Troubleshooting Guide

## Common Issues

### Mimo CLI not found
**Symptom**: "mimo: command not found" or analysis fails to start
**Fix**: Verify `~/.mimocode/bin/mimo` exists and is executable:
```bash
ls -la ~/.mimocode/bin/mimo
chmod +x ~/.mimocode/bin/mimo
```

### Database locked
**Symptom**: `sqlite3.OperationalError: database is locked`
**Fix**: Close any other connections to the DB. SQLAlchemy's session management should handle this, but WAL mode helps with concurrent reads. Wait a few seconds and retry.

### Job stuck in "processing"
**Symptom**: Job shows "processing" but nothing happens
**Fix**: The startup recovery hook marks stuck jobs as `failed` after restart. Or manually:
```sql
UPDATE pending_jobs SET status='failed' WHERE status='processing';
```

### Frontend shows "No career intelligence yet"
**Symptom**: Insights tab is empty after generation
**Fix**: Check `/api/insights/status` to see if generation completed. If failed, check `/api/generation-history` for error details.

### WebSocket not connecting
**Symptom**: Real-time updates not working
**Fix**: Ensure Flask-SocketIO is running on port 5000 with `async_mode='threading'`. Check browser console for connection errors.

### Build fails after rename
**Symptom**: "Could not load" errors in Vite build
**Fix**: Check import paths — all UI components are in `shared/ui/`, not `components/ui/`. Feature components are in `features/{name}/components/`.

### Tests fail with "no such column"
**Symptom**: DB schema mismatch in tests
**Fix**: Test fixtures need the same columns as production. Check `tests/conftest.py` for the shared fixture, and `tests/test_core/test_queue.py` for queue-specific fixtures.

## Debugging Tips

- **Backend**: Check `app/server/logs/` for structured logs
- **Frontend**: Use browser dev tools Network tab for API/WebSocket traffic
- **Database**: Use SQLAlchemy ORM models or Alembic for database operations. Never use raw SQL.
- **WebSocket**: SocketIO events visible in Network tab → WS connection → Messages
- **AI generation**: Check `/api/insights/progress` for real-time status
