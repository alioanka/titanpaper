# logger/trade_logger.py

import csv
import os
import time
from config import TRADE_LOG_PATH
from utils.terminal_logger import tlog

def log_trade(trade):
    fields = [
        "timestamp", "trade_id", "symbol", "side", "entry_price", "sl", "tp1", "tp2", "tp3",
        "strategy", "status", "ml_exit_reason", "ml_confidence", "ml_expected_pnl",
        "atr", "adx", "rsi", "macd", "ema_ratio"
    ]

    row = [
        time.strftime("%Y-%m-%d %H:%M:%S"),
        trade.get("trade_id"),
        trade.get("symbol"),
        trade.get("side"),
        trade.get("entry_price"),
        trade.get("sl"),
        trade["tp"][0] if len(trade["tp"]) > 0 else "",
        trade["tp"][1] if len(trade["tp"]) > 1 else "",
        trade["tp"][2] if len(trade["tp"]) > 2 else "",
        trade.get("strategy", "unknown"),
        trade.get("status", "open"),
        trade.get("ml_exit_reason", ""),
        round(float(trade.get("ml_confidence", 0)), 6),
        round(float(trade.get("ml_expected_pnl", 0)), 6),
        round(float(trade.get("atr", 0)), 6),
        round(float(trade.get("adx", 0)), 6),
        round(float(trade.get("rsi", 0)), 6),
        round(float(trade.get("macd", 0)), 6),
        round(float(trade.get("ema_ratio", 0)), 6)
    ]

    write_csv_row(TRADE_LOG_PATH, fields, row)
    tlog(f"📝 Trade logged: {trade.get('symbol')} | Side: {trade.get('side')} | Price: {trade.get('entry_price')}")

def write_csv_row(path, fields, row):
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quotechar='"', escapechar='\\')
        if not file_exists:
            writer.writerow(fields)
        writer.writerow(row)

def log_exit(trade):
    fields = [
        "timestamp", "trade_id", "symbol", "side", "exit_price",
        "status", "exit_reason", "tp_hits", "pnl",
        "strategy", "final_status", "ml_exit_reason", "ml_confidence", "ml_expected_pnl"
    ]

    try:
        pnl = round(float(trade.get("pnl", 0.0)), 6)
    except Exception as e:
        tlog(f"⚠️ PnL formatting error in trade_logger: {e} | value: {trade.get('pnl')}")
        pnl = 0.0

    row = [
        time.strftime("%Y-%m-%d %H:%M:%S"),
        trade.get("trade_id"),
        trade.get("symbol"),
        trade.get("side"),
        trade.get("exit_price"),
        trade.get("status"),
        trade.get("exit_reason"),
        ",".join([f"TP{i+1}" for i in trade.get("hit", [])]) if trade.get("hit") else "",
        pnl,
        trade.get("strategy", "unknown"),
        trade.get("status", "open"),
        trade.get("ml_exit_reason", ""),
        trade.get("ml_confidence", ""),
        trade.get("ml_expected_pnl", "")
    ]

    write_csv_row(TRADE_LOG_PATH, fields, row)
    tlog(f"📉 Trade closed: {trade.get('symbol')} | Exit: {trade.get('exit_reason')} | PnL: {pnl:.2f}%")
