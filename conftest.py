import os
import sys

# Ensures `src` is importable when running pytest from any working
# directory, regardless of pytest version or plugin configuration. This is
# a deliberate belt-and-suspenders alongside pytest.ini's `pythonpath = .`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
