# logger/balance_tracker.py

import os
import csv
import time
from config import BALANCE_LOG_PATH, INITIAL_BALANCE

def load_last_balance():
    """
    Returns the most recent balance from file or fallback to initial.
    """
    if not os.path.exists(BALANCE_LOG_PATH):
        return INITIAL_BALANCE

    with open(BALANCE_LOG_PATH, "r") as f:
        lines = f.readlines()
        if not lines or len(lines) < 2:
            return INITIAL_BALANCE
        last = lines[-1].strip().split(",")
        return float(last[1])


def update_balance(new_balance):
    """
    Appends new balance snapshot to balance history.
    """
    new_file = not os.path.exists(BALANCE_LOG_PATH)
    with open(BALANCE_LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "balance"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), round(new_balance, 2)])
