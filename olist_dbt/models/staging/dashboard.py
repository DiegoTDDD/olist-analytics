"""Entry point kept for the deployed app: runs the dashboard at the repository root.

An earlier deployment pointed Streamlit Community Cloud at this path. The real
dashboard is ../../../dashboard.py; this file only runs it, so both paths work.
dbt ignores this file (see olist_dbt/.dbtignore).
"""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parents[3] / "dashboard.py"), run_name="__main__")
