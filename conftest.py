"""
pytest conftest.py — adds project root to sys.path so all modules are importable.
"""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))
