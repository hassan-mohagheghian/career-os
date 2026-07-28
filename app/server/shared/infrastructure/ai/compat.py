"""AI module compatibility — ensures app.ai is importable from the server.

The server runs from app/server/, but the AI layer lives at app/ai/.
This module adds the parent directory to sys.path so imports work.
"""

import os
import sys

_server_dir = os.path.dirname(os.path.abspath(__file__))
_app_dir = os.path.abspath(os.path.join(_server_dir, '..', '..', '..', '..'))

if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)


def get_llm_service(*args, **kwargs):
    """Lazy import of LLMService — avoids circular imports at module load time."""
    from ai.service import get_llm_service as _get
    return _get(*args, **kwargs)
