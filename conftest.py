"""Root conftest.py for pytest configuration."""

import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent
src_dir = project_root / "src"
tests_dir = project_root / "tests"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(tests_dir))
