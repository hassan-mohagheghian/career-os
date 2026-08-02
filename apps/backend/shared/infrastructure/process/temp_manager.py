from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, List, Optional, Set


class TempFileManager:
    _instance: Optional[TempFileManager] = None

    def __new__(cls) -> TempFileManager:
        if cls._instance is None:
            inst = super().__new__(cls)
            cls._instance = inst
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def __init__(self) -> None:
        if not hasattr(self, '_files'):
            self._files: Dict[str, Set[str]] = defaultdict(set)

    def register(self, job_key: str, path: str) -> None:
        self._files[job_key].add(path)

    def cleanup(self, job_key: str) -> int:
        paths = self._files.pop(job_key, set())
        count = 0
        for p in paths:
            try:
                os.remove(p)
                count += 1
            except OSError:
                pass
        return count

    def cleanup_all(self) -> int:
        total = 0
        for job_key in list(self._files):
            total += self.cleanup(job_key)
        return total
