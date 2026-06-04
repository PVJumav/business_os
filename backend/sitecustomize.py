"""Make backend package imports work when hosts set the backend folder as root."""

from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent
repo_root_text = str(repo_root)

if repo_root_text not in sys.path:
    sys.path.insert(0, repo_root_text)
