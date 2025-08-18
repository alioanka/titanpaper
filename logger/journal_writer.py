# logger/journal_writer.py
import csv
import os
import time
from config import JOURNAL_PATH
from utils.pnl_utils import calc_realistic_pnl
from utils.terminal_logger import tlog

_FIELDS = [
    "timestamp","trade_id","symbol","side","entry_price","exit_price",
    "status","exit_reason","tp_hits","pnl","duration_sec","balance","strategy",
    "ml_exit_reason","ml_confidence","ml_expected_pnl","atr","adx","rsi","macd","ema_ratio"
]

def _write(path, fields, row):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quotechar='"', escapechar='\\')
        if new_file:
            w.writerow(fields)
        w.writerow(row)

def update_journal(trade: dict):
    """
    Append a closed-trade record into journal.csv.
    """
    if str(trade.get("status","")).lower() != "closed":
        return

    try:
        pnl = calc_realistic_pnl(trade.get("entry_price"), trade.get("exit_price"), trade.get("side","LONG"), trade.get("leverage",1))
    except Exception:
        pnl = 0.0

    row = [
        time.strftime("%Y-%m-%d %H:%M:%S"),
        trade.get("trade_id"),
        trade.get("symbol"),
        trade.get("side"),
        trade.get("entry_price"),
        trade.get("exit_price"),
        "closed",
        trade.get("exit_reason"),
        ",".join([f"TP{i+1}" for i in trade.get("hit", [])]) if trade.get("hit") else "",
        pnl,
        trade.get("duration_sec",0),
        trade.get("balance",""),
        trade.get("strategy",""),
        trade.get("ml_exit_reason",""),
        trade.get("ml_confidence",""),
        trade.get("ml_expected_pnl",""),
        trade.get("atr",""),
        trade.get("adx",""),
        trade.get("rsi",""),
        trade.get("macd",""),
        trade.get("ema_ratio",""),
    ]
    _write(JOURNAL_PATH, _FIELDS, row)
    tlog(f"📘 Journal updated: {trade.get('symbol')} | Exit: {trade.get('exit_reason')} | PnL: {pnl:.4f}%")
