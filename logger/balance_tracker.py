# logger/balance_tracker.py

import os
import csv
import time
from config import BALANCE_LOG_PATH, INITIAL_BALANCE

def _ensure_parent_dir(path: str):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def load_last_balance():
    """
    Returns the most recent balance from file or fallback to initial.
    Gracefully handles a missing or empty file.
    """
    # If the file doesn't exist yet, return initial balance
    if not os.path.exists(BALANCE_LOG_PATH):
        return INITIAL_BALANCE

    try:
        with open(BALANCE_LOG_PATH, "r", encoding="utf-8") as f:
            # Keep only data lines (skip header lines)
            lines = [line.strip() for line in f if "," in line and not line.lower().startswith("timestamp")]
        if not lines:
            return INITIAL_BALANCE

        # Last CSV line format: "YYYY-mm-dd HH:MM:SS,<balance>"
        last = lines[-1].split(",")
        if len(last) >= 2:
            return float(last[-1])
        return INITIAL_BALANCE

    except Exception as e:
        print(f"⚠️ Error reading last balance: {e}")
        return INITIAL_BALANCE

def update_balance(new_balance):
    """
    Appends new balance snapshot to balance history.
    Ensures directory exists and writes CSV header once.
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
