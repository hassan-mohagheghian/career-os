"""Unit test conftest - overrides root conftest fixtures to prevent conflicts."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
