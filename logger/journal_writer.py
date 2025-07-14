# logger/journal_writer.py

import csv
import os
import time
from config import JOURNAL_PATH
from logger.balance_tracker import load_last_balance
from utils.pnl_utils import calc_realistic_pnl



def update_journal(trade):
    fields = [
        "timestamp", "trade_id", "symbol", "side", "entry_price", "exit_price",
        "status", "exit_reason", "tp_hits", "pnl", "duration_sec", "balance", "strategy",
        "ml_exit_reason", "ml_confidence", "ml_expected_pnl", "atr", "adx", "rsi", "macd", "ema_ratio"
    ]



    now = time.time()
    entry_time = trade.get("entry_time", now)
    duration = int(now - entry_time)
    trade["pnl"] = calc_realistic_pnl(
        trade.get("entry_price"),
        trade.get("exit_price"),
        trade.get("side"),
        trade.get("leverage", 1)
    )
    try:
        pnl = round(float(trade.get("pnl", 0.0)), 6)
    except Exception as e:
        print(f"⚠️ PnL formatting error: {e} | raw value: {trade.get('pnl')}")
        pnl = 0.0

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
        pnl,
        duration,
        load_last_balance(),
        trade.get("strategy", "unknown"),
        trade.get("ml_exit_reason", ""),
        trade.get("ml_confidence", ""),
        trade.get("ml_expected_pnl", ""),
        trade.get("atr", ""),
        trade.get("adx", ""),
        trade.get("rsi", ""),
        trade.get("macd", ""),
        trade.get("ema_ratio", "")
    ]


    write_csv_row(JOURNAL_PATH, fields, row)


def write_csv_row(path, fields, row):
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(fields)
        writer.writerow(row)
