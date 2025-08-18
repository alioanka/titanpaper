# logger/trade_logger.py
import csv
import os
import time
from config import TRADE_LOG_PATH
from utils.terminal_logger import tlog

_OPEN_FIELDS = [
    "timestamp","trade_id","symbol","side","entry_price","sl","tp1","tp2","tp3",
    "strategy","status","ml_exit_reason","ml_confidence","ml_expected_pnl",
    "atr","adx","rsi","macd","ema_ratio"
]

_CLOSE_FIELDS = [
    "timestamp","trade_id","symbol","side","entry_price","exit_price","status",
    "exit_reason","tp_hits","pnl","strategy","ml_exit_reason","ml_confidence",
    "ml_expected_pnl","atr","adx","rsi","macd","ema_ratio"
]

def _write(path, fields, row):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quotechar='"', escapechar='\\')
        if new_file:
            w.writerow(fields)
        w.writerow(row)

def log_trade(trade: dict):
    row = [
        time.strftime("%Y-%m-%d %H:%M:%S"),
        trade.get("trade_id"),
        trade.get("symbol"),
        trade.get("side"),
        trade.get("entry_price"),
        trade.get("sl"),
        trade.get("tp1"),
        trade.get("tp2"),
        trade.get("tp3"),
        trade.get("strategy","unknown"),
        trade.get("status","open"),
        trade.get("ml_exit_reason",""),
        trade.get("ml_confidence",""),
        trade.get("ml_expected_pnl",""),
        trade.get("atr",""),
        trade.get("adx",""),
        trade.get("rsi",""),
        trade.get("macd",""),
        trade.get("ema_ratio",""),
    ]
    _write(TRADE_LOG_PATH, _OPEN_FIELDS, row)
    tlog(f"📝 Trade open logged: {trade.get('symbol')} {trade.get('side')} @ {trade.get('entry_price')}")

def log_exit(trade: dict, pnl_pct: float, tp_hits: str):
    row = [
        time.strftime("%Y-%m-%d %H:%M:%S"),
        trade.get("trade_id"),
        trade.get("symbol"),
        trade.get("side"),
        trade.get("entry_price"),
        trade.get("exit_price"),
        "closed",
        trade.get("exit_reason"),
        tp_hits,
        round(float(pnl_pct),4),
        trade.get("strategy","unknown"),
        trade.get("ml_exit_reason",""),
        trade.get("ml_confidence",""),
        trade.get("ml_expected_pnl",""),
        trade.get("atr",""),
        trade.get("adx",""),
        trade.get("rsi",""),
        trade.get("macd",""),
        trade.get("ema_ratio",""),
    ]
    _write(TRADE_LOG_PATH, _CLOSE_FIELDS, row)
    tlog(f"📉 Trade closed: {trade.get('symbol')} | Exit: {trade.get('exit_reason')} | PnL: {pnl_pct:.2f}%")
