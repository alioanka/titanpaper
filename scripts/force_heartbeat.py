# scripts/force_heartbeat.py
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, ".."))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)

from logger.balance_tracker import load_last_balance, update_balance

if __name__ == "__main__":
    update_balance(load_last_balance())
    print("Heartbeat written to balance_history.csv")
