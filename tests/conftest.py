"""
Pytest configuration file
This file ensures that the project root is in the Python path
so that flask_app can be imported properly.
"""

import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
