"""Background application entrypoint for the Job Search Intelligence platform.

Starts ARQ worker with Redis queue connection.

Usage:
    python -m background.main
    BACKGROUND_WORKER=true python app/start.py dev
"""

import os
import sys

_server_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "server")
)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from background.entrypoint import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
