# utils/ml_logger.py
import csv
import os
from datetime import datetime
from utils.pnl_utils import calc_realistic_pnl
from utils.terminal_logger import tlog
from config import ML_LOG_FILE

_HEADERS = [
    "timestamp","id","symbol","side","entry_price","exit_price","exit_reason",
    "sl","tp1","tp2","tp3","atr","trend_strength","volatility","adx","rsi",
    "macd","ema_ratio","pnl_pct","raw_profit","duration_sec","strategy","leverage","is_partial"
]

def log_ml_features(trade: dict, trend: float, volatility: float, atr: float):
    # Only log on final close
    if str(trade.get("status","")).lower() != "closed":
        return

    try:
        entry_price = float(trade.get("entry_price"))
        exit_price  = float(trade.get("exit_price"))
        side        = trade.get("side","LONG")
        leverage    = float(trade.get("leverage",1))
    except Exception:
        return

    pnl_pct   = calc_realistic_pnl(entry_price, exit_price, side, leverage)
    raw_profit = 0.0  # keep 0 unless you have notional

    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "id": trade.get("trade_id"),
        "symbol": trade.get("symbol"),
        "side": side,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "exit_reason": trade.get("exit_reason",""),
        "sl": trade.get("sl",""),
        "tp1": trade.get("tp1",""),
        "tp2": trade.get("tp2",""),
        "tp3": trade.get("tp3",""),
        "atr": round(float(atr or 0),5),
        "trend_strength": round(float(trend or 0),5),
        "volatility": round(float(volatility or 0),5),
        "adx": round(float(trade.get("adx",0)),5),
        "rsi": round(float(trade.get("rsi",0)),5),
        "macd": round(float(trade.get("macd",0)),5),
        "ema_ratio": round(float(trade.get("ema_ratio",1)),5),
        "pnl_pct": pnl_pct,
        "raw_profit": raw_profit,
        "duration_sec": trade.get("duration_sec",0),
        "strategy": trade.get("strategy",""),
        "leverage": leverage,
        "is_partial": 1 if "Partial" in str(trade.get("exit_reason","")) else 0
    }

    new_file = not os.path.exists(ML_LOG_FILE)
    with open(ML_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_HEADERS, extrasaction="ignore")
        if new_file:
            w.writeheader()
        w.writerow(row)

    tlog(f"📦 ML logged: {row['symbol']} | {row['exit_reason']} | PnL: {pnl_pct:.2f}%")
