# logger/balance_tracker.py

import os
import csv
import time
from config import BALANCE_LOG_PATH, INITIAL_BALANCE

def load_last_balance():
    if not os.path.exists(BALANCE_LOG_PATH):
        return INITIAL_BALANCE

    with open(BALANCE_LOG_PATH, "r") as f:
        lines = [line.strip() for line in f if "," in line and not line.startswith("timestamp")]
        if not lines:
            return INITIAL_BALANCE
        try:
            last = lines[-1].split(",")
            return float(last[1])
        except Exception as e:
            print(f"⚠️ Error loading balance: {e}")
            return INITIAL_BALANCE



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
