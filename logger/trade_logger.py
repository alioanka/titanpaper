# logger/trade_logger.py
import csv
import os
import time
from config import TRADE_LOG_PATH
from utils.terminal_logger import tlog

# A single, stable schema used for both OPEN and CLOSED rows
_FIELDS = [
    "timestamp","trade_id","symbol","side",
    "entry_price","sl","tp1","tp2","tp3",     # planned levels (known at open)
    "exit_price","status","exit_reason","tp_hits","pnl",  # filled on close
    "strategy","ml_exit_reason","ml_confidence","ml_expected_pnl",
    "atr","adx","rsi","macd","ema_ratio"
]

def _ensure_header(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new_file = not os.path.exists(path)
    if new_file or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f, quotechar='"', escapechar='\\').writerow(_FIELDS)

def _append_row(path, row_dict):
    _ensure_header(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore", quotechar='"', escapechar='\\')
        w.writerow(row_dict)

def log_trade(trade: dict):
    """
    Log an OPEN trade using the unified schema (exit columns left blank).
    """
    row = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "trade_id": trade.get("trade_id"),
        "symbol": trade.get("symbol"),
        "side": trade.get("side"),
        "entry_price": trade.get("entry_price"),
        "sl": trade.get("sl"),
        "tp1": trade.get("tp1"),
        "tp2": trade.get("tp2"),
        "tp3": trade.get("tp3"),
        "exit_price": "",
        "status": trade.get("status","open"),
        "exit_reason": "",
        "tp_hits": "",
        "pnl": "",
        "strategy": trade.get("strategy","unknown"),
        "ml_exit_reason": trade.get("ml_exit_reason",""),
        "ml_confidence": trade.get("ml_confidence",""),
        "ml_expected_pnl": trade.get("ml_expected_pnl",""),
        "atr": trade.get("atr",""),
        "adx": trade.get("adx",""),
        "rsi": trade.get("rsi",""),
        "macd": trade.get("macd",""),
        "ema_ratio": trade.get("ema_ratio",""),
    }
    _append_row(TRADE_LOG_PATH, row)
    tlog(f"📝 Trade open logged: {trade.get('symbol')} {trade.get('side')} @ {trade.get('entry_price')}")

def log_exit(trade: dict, pnl_pct: float, tp_hits: str):
    """
    Log a CLOSED trade using the same schema (fills exit columns).
    """
    row = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "trade_id": trade.get("trade_id"),
        "symbol": trade.get("symbol"),
        "side": trade.get("side"),
        "entry_price": trade.get("entry_price"),
        "sl": trade.get("sl"),
        "tp1": trade.get("tp1"),
        "tp2": trade.get("tp2"),
        "tp3": trade.get("tp3"),
        "exit_price": trade.get("exit_price"),
        "status": "closed",
        "exit_reason": trade.get("exit_reason"),
        "tp_hits": tp_hits,
        "pnl": round(float(pnl_pct),4),
        "strategy": trade.get("strategy","unknown"),
        "ml_exit_reason": trade.get("ml_exit_reason",""),
        "ml_confidence": trade.get("ml_confidence",""),
        "ml_expected_pnl": trade.get("ml_expected_pnl",""),
        "atr": trade.get("atr",""),
        "adx": trade.get("adx",""),
        "rsi": trade.get("rsi",""),
        "macd": trade.get("macd",""),
        "ema_ratio": trade.get("ema_ratio",""),
    }
    _append_row(TRADE_LOG_PATH, row)
    tlog(f"📉 Trade closed: {trade.get('symbol')} | Exit: {trade.get('exit_reason')} | PnL: {pnl_pct:.2f}%")
