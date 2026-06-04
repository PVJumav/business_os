"""Compatibility shim for hosts that use the backend directory as project root."""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent)]
