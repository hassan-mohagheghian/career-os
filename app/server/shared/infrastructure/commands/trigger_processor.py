#!/usr/bin/env python3
"""
Trigger processor - watches for process trigger files and outputs pending jobs
that need processing. This is called by the AI provider to pick up jobs from the UI.
"""
import os
import json
import glob
from shared.infrastructure.process.logging_config import get_logger

log = get_logger('commands.trigger_processor')

QUEUE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '.queue')

def get_pending_triggers():
    """Get all pending trigger files."""
    os.makedirs(QUEUE_DIR, exist_ok=True)
    triggers = []
    for f in sorted(glob.glob(os.path.join(QUEUE_DIR, 'process_*.json'))):
        try:
            with open(f) as fh:
                data = json.load(fh)
                data['_file'] = f
                triggers.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return triggers

def complete_trigger(trigger_file, success=True, error=None):
    """Mark a trigger as completed and remove the file."""
    if os.path.exists(trigger_file):
        os.remove(trigger_file)

if __name__ == '__main__':
    triggers = get_pending_triggers()
    if triggers:
        log.info("Pending triggers", count=len(triggers))
        for t in triggers:
            log.info("Trigger", data=json.dumps(t, indent=2))
    else:
        log.info("No pending triggers")
