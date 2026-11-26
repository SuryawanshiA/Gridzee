"""AI engine: explore, plan, generate, run with retries, and heal, with human approval gates.

It may import the test framework (``src/gridzee_qa``). The framework never imports it.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
