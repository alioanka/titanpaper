# logger/balance_tracker.py

import os
import csv
import time
from config import BALANCE_LOG_PATH, INITIAL_BALANCE

def load_last_balance():
    """Returns the most recent balance from file or fallback to initial."""
    if not os.path.exists(BALANCE_LOG_PATH):
        return INITIAL_BALANCE

    try:
        with open(BALANCE_LOG_PATH, "r") as f:
            # Skip header, keep only lines with 2 columns
            lines = [line.strip() for line in f if "," in line and not line.startswith("timestamp")]

            if not lines:
                return INITIAL_BALANCE

            last = lines[-1].split(",")
            if len(last) < 2:
                raise ValueError(f"Malformed last balance row: {last}")

            return float(last[1])
    except Exception as e:
        print(f"⚠️ Error reading last balance: {e}")
        return INITIAL_BALANCE




def update_balance(new_balance):
    """ Appends new balance snapshot to balance history. """
    try:
        balance_value = round(float(new_balance), 2)
    except Exception as e:
        print(f"⚠️ Error rounding balance: {e} | raw value: {new_balance}")
        balance_value = round(INITIAL_BALANCE, 2)

    new_file = not os.path.exists(BALANCE_LOG_PATH)
    with open(BALANCE_LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "balance"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), balance_value])

