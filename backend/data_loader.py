"""Load Pretty Fly CSVs into pandas and run the pack reconciliation validator."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

import re

from config import DEFAULT_DATA_DIR, VALIDATE_SCRIPT

# Rule descriptions aligned with validate.py RULES tuple
RULE_DESCRIPTIONS: dict[int, str] = {
    1: "Order subtotals = sum of line items",
    2: "Customer total_spent and orders_count match orders",
    3: "Discount code usage_count = orders using that code",
    4: "Every line item produces inventory movement (sale)",
    5: "Every PO receipt produces inventory movement (po_receipt)",
    6: "Every refund -> inventory return + bank txn",
    7: "Inventory movements sum to current stock level",
    8: "Monthly Google ad spend = Google bank transactions",
    9: "Monthly Meta ad spend = Meta bank transactions",
    10: "UTM campaign names in orders exist in ads/email",
    11: "Email attributed_orders/revenue match orders",
    12: "Klaviyo subscription appears monthly in bank",
    13: "PO payments in bank = purchase_orders.total_cost_gbp",
    14: "Running bank balance internally consistent",
    15: "Net Sales = subtotals - discounts - refunds",
    16: "COGS = sum(units sold x landed cost)",
    17: "Inventory value = quantity x landed cost",
    18: "Accounts Payable = outstanding PO balances",
    19: "Support ticket FK references all exist",
    20: "UTM campaign names consistent across all tables",
}


def parse_validation_output(output: str) -> list[dict[str, Any]]:
    """Parse validate.py stdout into structured rule results."""
    failures: list[dict[str, Any]] = []
    rule_pattern = re.compile(r"\[(PASS|FAIL|SKIP)\] Rule\s+(\d+):\s*(.+)")
    current: dict[str, Any] | None = None

    for line in output.splitlines():
        match = rule_pattern.match(line.strip())
        if match:
            if current is not None:
                failures.append(current)
            status, num, desc = match.groups()
            current = {
                "rule_number": int(num),
                "description": desc.strip(),
                "status": status,
                "message": None,
            }
            continue
        if current is not None and line.strip().startswith(" "):
            msg_line = line.strip()
            if msg_line:
                current["message"] = (
                    f"{current['message']}\n{msg_line}"
                    if current["message"]
                    else msg_line
                )

    if current is not None:
        failures.append(current)

    if not failures:
        for num, desc in RULE_DESCRIPTIONS.items():
            failures.append(
                {
                    "rule_number": num,
                    "description": desc,
                    "status": "PASS" if "passed" in output.lower() else "FAIL",
                    "message": None,
                }
            )
    return failures


# Files required by CashFly computation (PROMPT_01 + TRD core tables)
REQUIRED_CSVS: dict[str, dict[str, Any]] = {
    "orders": {"file": "orders.csv", "parse_dates": ["created_at"]},
    "line_items": {"file": "line_items.csv", "parse_dates": []},
    "variants": {"file": "variants.csv", "parse_dates": []},
    "products": {"file": "products.csv", "parse_dates": ["created_at"]},
    "inventory_movements": {
        "file": "inventory_movements.csv",
        "parse_dates": ["date"],
    },
    "po_line_items": {"file": "po_line_items.csv", "parse_dates": []},
    "purchase_orders": {
        "file": "purchase_orders.csv",
        "parse_dates": [
            "created_at",
            "expected_delivery",
            "actual_delivery",
            "deposit_paid_at",
            "balance_paid_at",
        ],
    },
    "bank_transactions": {
        "file": "bank_transactions.csv",
        "parse_dates": ["date"],
    },
    "google_ads_daily": {
        "file": "google_ads_daily.csv",
        "parse_dates": ["date"],
    },
    "meta_ads_daily": {
        "file": "meta_ads_daily.csv",
        "parse_dates": ["date"],
    },
    "email_campaigns": {"file": "email_campaigns.csv", "parse_dates": []},
    "email_events": {"file": "email_events.csv", "parse_dates": []},
}

# Optional enrichment tables (loaded when present)
OPTIONAL_CSVS: dict[str, dict[str, Any]] = {
    "customers": {"file": "customers.csv", "parse_dates": []},
    "addresses": {"file": "addresses.csv", "parse_dates": []},
    "suppliers": {"file": "suppliers.csv", "parse_dates": []},
    "refunds": {"file": "refunds.csv", "parse_dates": []},
    "discount_codes": {"file": "discount_codes.csv", "parse_dates": []},
    "collections": {"file": "collections.csv", "parse_dates": []},
    "product_collections": {"file": "product_collections.csv", "parse_dates": []},
    "support_tickets": {"file": "support_tickets.csv", "parse_dates": []},
}


class DataLoader:
    """Load CSV data from a Pretty Fly data directory and validate reconciliation."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        if not self.data_dir.is_dir():
            raise FileNotFoundError(
                f"Data directory not found: {self.data_dir}. "
                "Point to pretty_fly_data_pack/data or copy CSVs into ./data/"
            )

    def _read_csv(self, filename: str, parse_dates: list[str]) -> pd.DataFrame:
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing required data file: {filename}")
        kwargs: dict[str, Any] = {}
        if parse_dates:
            kwargs["parse_dates"] = parse_dates
        return pd.read_csv(path, **kwargs)

    def _load_table_specs(
        self, specs: dict[str, dict[str, Any]], required: bool
    ) -> dict[str, pd.DataFrame]:
        dfs: dict[str, pd.DataFrame] = {}
        for key, spec in specs.items():
            path = self.data_dir / spec["file"]
            if not path.exists():
                if required:
                    raise FileNotFoundError(f"Missing required data file: {spec['file']}")
                continue
            dfs[key] = self._read_csv(spec["file"], spec.get("parse_dates", []))
        return dfs

    def run_validation(self) -> dict[str, Any]:
        """Run pretty_fly_data_pack/validate.py against this data directory."""
        script = VALIDATE_SCRIPT
        if not script.exists():
            # Allow validate.py colocated with data_dir parent
            alt = self.data_dir.parent / "validate.py"
            script = alt if alt.exists() else script

        if not script.exists():
            return {
                "passed": False,
                "output": f"validate.py not found at {VALIDATE_SCRIPT}",
                "exit_code": -1,
            }

        env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
        result = subprocess.run(
            [sys.executable, str(script), str(self.data_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(script.parent),
            env=env,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return {
            "passed": result.returncode == 0,
            "output": output.strip(),
            "exit_code": result.returncode,
            "failures": parse_validation_output(output.strip()),
        }

    def load(self, *, run_validator: bool = True) -> dict[str, Any]:
        """
        Load all CSVs and optionally run validate.py.

        Returns:
            {"dfs": dict[str, DataFrame], "validation": {"passed": bool, "output": str}}
        """
        dfs = self._load_table_specs(REQUIRED_CSVS, required=True)
        dfs.update(self._load_table_specs(OPTIONAL_CSVS, required=False))

        validation = (
            self.run_validation()
            if run_validator
            else {"passed": True, "output": "skipped", "exit_code": 0, "failures": []}
        )
        return {"dfs": dfs, "validation": validation}
