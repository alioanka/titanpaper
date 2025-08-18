# scripts/migrate_trade_log.py
import os
import sys
import time
import pandas as pd
from datetime import datetime
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, ".."))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)

from config import TRADE_LOG_PATH

FIELDS = [
    "timestamp","trade_id","symbol","side",
    "entry_price","sl","tp1","tp2","tp3",
    "exit_price","status","exit_reason","tp_hits","pnl",
    "strategy","ml_exit_reason","ml_confidence","ml_expected_pnl",
    "atr","adx","rsi","macd","ema_ratio"
]

def backup_path(path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{path}.backup_{ts}.csv"

def main():
    if not os.path.exists(TRADE_LOG_PATH) or os.path.getsize(TRADE_LOG_PATH)==0:
        print("trade_log.csv not found or empty. Nothing to migrate.")
        return
    df = pd.read_csv(TRADE_LOG_PATH, dtype=str)  # read raw as strings to preserve weird rows
    df = df.fillna("")

    # identify legacy close rows (tp1 == 'closed' case)
    is_legacy_close = df.get("tp1","").str.lower().eq("closed")
    is_open = df.get("status","").str.lower().eq("open")

    rows = []
    for _, r in df.iterrows():
        if str(r.get("status","")).lower() == "open" and not is_legacy_close.loc[_]:
            # OPEN row in old schema → map directly, leave exit fields blank
            rows.append({
                "timestamp": r.get("timestamp",""),
                "trade_id": r.get("trade_id",""),
                "symbol": r.get("symbol",""),
                "side": r.get("side",""),
                "entry_price": r.get("entry_price",""),
                "sl": r.get("sl",""),
                "tp1": r.get("tp1",""),
                "tp2": r.get("tp2",""),
                "tp3": r.get("tp3",""),
                "exit_price": "",
                "status": "open",
                "exit_reason": "",
                "tp_hits": "",
                "pnl": "",
                "strategy": r.get("strategy",""),
                "ml_exit_reason": r.get("ml_exit_reason",""),
                "ml_confidence": r.get("ml_confidence",""),
                "ml_expected_pnl": r.get("ml_expected_pnl",""),
                "atr": r.get("atr",""),
                "adx": r.get("adx",""),
                "rsi": r.get("rsi",""),
                "macd": r.get("macd",""),
                "ema_ratio": r.get("ema_ratio",""),
            })
        elif str(r.get("tp1","")).lower() == "closed":
            # LEGACY CLOSED row: re-map positions as per observed misalignment
            rows.append({
                "timestamp": r.get("timestamp",""),
                "trade_id": r.get("trade_id",""),
                "symbol": r.get("symbol",""),
                "side": r.get("side",""),
                "entry_price": r.get("entry_price",""),
                "sl": "",  # unknown here (original got overwritten)
                "tp1": "", "tp2": "", "tp3": "",
                "exit_price": r.get("sl",""),            # <- exit_price was placed in 'sl'
                "status": "closed",
                "exit_reason": r.get("tp2",""),          # <- exit_reason was in 'tp2'
                "tp_hits": r.get("tp3",""),              # may be blank/NaN
                "pnl": r.get("strategy",""),             # <- pnl ended up in 'strategy'
                "strategy": r.get("status",""),          # <- strategy was in 'status'
                "ml_exit_reason": r.get("ml_exit_reason",""),
                "ml_confidence": r.get("ml_confidence",""),
                "ml_expected_pnl": r.get("ml_expected_pnl",""),
                "atr": r.get("atr",""),
                "adx": r.get("adx",""),
                "rsi": r.get("rsi",""),
                "macd": r.get("macd",""),
                "ema_ratio": r.get("ema_ratio",""),
            })
        else:
            # Unknown row — keep as best-effort open
            rows.append({
                "timestamp": r.get("timestamp",""),
                "trade_id": r.get("trade_id",""),
                "symbol": r.get("symbol",""),
                "side": r.get("side",""),
                "entry_price": r.get("entry_price",""),
                "sl": r.get("sl",""),
                "tp1": r.get("tp1",""),
                "tp2": r.get("tp2",""),
                "tp3": r.get("tp3",""),
                "exit_price": r.get("exit_price","") if "exit_price" in r else "",
                "status": r.get("status",""),
                "exit_reason": r.get("exit_reason","") if "exit_reason" in r else "",
                "tp_hits": r.get("tp_hits","") if "tp_hits" in r else "",
                "pnl": r.get("pnl","") if "pnl" in r else "",
                "strategy": r.get("strategy",""),
                "ml_exit_reason": r.get("ml_exit_reason",""),
                "ml_confidence": r.get("ml_confidence",""),
                "ml_expected_pnl": r.get("ml_expected_pnl",""),
                "atr": r.get("atr",""),
                "adx": r.get("adx",""),
                "rsi": r.get("rsi",""),
                "macd": r.get("macd",""),
                "ema_ratio": r.get("ema_ratio",""),
            })

    backup = backup_path(TRADE_LOG_PATH)
    os.replace(TRADE_LOG_PATH, backup)
    out = pd.DataFrame(rows, columns=FIELDS)
    out.to_csv(TRADE_LOG_PATH, index=False)
    print(f"Migrated trade_log.csv. Backup saved at: {backup}")
    print(f"New rows: {len(out)} | Closed detected: {int((out['status'].astype(str).str.lower()=='closed').sum())}")

if __name__ == "__main__":
    main()
