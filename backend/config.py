"""Shared constants for CashFly data and computation."""

from datetime import date
from pathlib import Path

# "Today" in the Pretty Fly dataset (see pretty_fly_data_pack/README.md)
DATASET_TODAY: date = date(2026, 6, 1)

# Default path to hackathon CSVs (relative to backend/)
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "pretty_fly_data_pack" / "data"
VALIDATE_SCRIPT = REPO_ROOT / "pretty_fly_data_pack" / "validate.py"

# API display limits (dashboard headline uses top leaks, not full dead-stock set)
TOP_LEAKS_LIMIT = 10
BACKTEST_HORIZON_DAYS = 30
