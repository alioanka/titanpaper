# logger/balance_tracker.py
import os
import csv
import time
from typing import Optional
from config import BALANCE_LOG_PATH, INITIAL_BALANCE

def _ensure_parent_dir(path: str):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def _read_last_csv_row(path: str) -> Optional[list]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            last = None
            for row in csv.reader(f):
                if row and row[0] != "timestamp":
                    last = row
            return last
    except Exception:
        return None

def load_last_balance() -> float:
    """
    Returns the most recent balance from file or INITIAL_BALANCE.
    """
    try:
        if not os.path.exists(BALANCE_LOG_PATH) or os.path.getsize(BALANCE_LOG_PATH) == 0:
            return round(INITIAL_BALANCE, 2)
        last = _read_last_csv_row(BALANCE_LOG_PATH)
        if not last:
            return round(INITIAL_BALANCE, 2)
        bal = float(last[1])
        return round(bal, 2)
    except Exception as e:
        print(f"⚠️ load_last_balance error: {e}")
        return round(INITIAL_BALANCE, 2)

def update_balance(new_balance: float):
    """
    Append a balance snapshot as (timestamp, balance). Never crashes the loop.
    """
    try:
        balance_value = round(float(new_balance), 2)
    except Exception as e:
        print(f"⚠️ Error rounding balance: {e} | raw value: {new_balance}")
        balance_value = round(INITIAL_BALANCE, 2)

    _ensure_parent_dir(BALANCE_LOG_PATH)
    new_file = not os.path.exists(BALANCE_LOG_PATH)

    try:
        with open(BALANCE_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["timestamp", "balance"])
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), balance_value])
    except Exception as e:
        print(f"⚠️ Error writing balance history: {e}")
