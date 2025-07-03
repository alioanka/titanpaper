# logger/journal_writer.py

import csv
import os
import time
from config import JOURNAL_PATH
from logger.balance_tracker import load_last_balance
from utils.pnl_utils import calc_fake_pnl


def update_journal(trade):
    fields = [
        "timestamp", "trade_id", "symbol", "side", "entry_price", "exit_price",
        "status", "exit_reason", "tp_hits", "pnl", "duration_sec", "balance", "strategy"
    ]

    now = time.time()
    entry_time = trade.get("entry_time", now)
    duration = int(now - entry_time)
    trade["pnl"] = calc_fake_pnl(trade)  # <-- 🔧 Force accurate PnL
    row = [
        time.strftime("%Y-%m-%d %H:%M:%S"),
        trade.get("trade_id"),
        trade.get("symbol"),
        trade.get("side"),
        trade.get("entry_price"),
        trade.get("exit_price"),
        trade.get("status"),
        trade.get("exit_reason"),
        ",".join([f"TP{i+1}" for i in trade.get("hit", [])]) if trade.get("hit") else "",
        round(trade.get("pnl", 0.0), 6),
        duration,
        load_last_balance(),
        trade.get("strategy", "unknown")
    ]

    write_csv_row(JOURNAL_PATH, fields, row)


def write_csv_row(path, fields, row):
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(fields)
        writer.writerow(row)
