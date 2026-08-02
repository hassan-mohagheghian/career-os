"""AI module compatibility — ensures ai.infrastructure is importable from the backend."""

import os
import sys

_server_dir = os.path.dirname(os.path.abspath(__file__))
_app_server_dir = os.path.abspath(os.path.join(_server_dir, '..', '..', '..'))

if _app_server_dir not in sys.path:
    sys.path.insert(0, _app_server_dir)


def get_llm_service(*args, **kwargs):
    """Lazy import of LLMService — avoids circular imports at module load time."""
    from ai.infrastructure.service import get_llm_service as _get
    return _get(*args, **kwargs)
