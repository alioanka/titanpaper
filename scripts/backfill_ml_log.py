# scripts/backfill_ml_log.py
import os
import csv
import pandas as pd
from datetime import datetime
from config import JOURNAL_PATH, ML_LOG_FILE

ML_HEADERS = [
    "timestamp","id","symbol","side","entry_price","exit_price","exit_reason",
    "sl","tp1","tp2","tp3","atr","trend_strength","volatility","adx","rsi",
    "macd","ema_ratio","pnl_pct","raw_profit","duration_sec","strategy","leverage","is_partial"
]

def _read_csv(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    return pd.read_csv(path, encoding="utf-8")

def _ensure_ml_headers(path):
    new_file = not os.path.exists(path)
    if new_file:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(ML_HEADERS)

def main():
    jdf = _read_csv(JOURNAL_PATH)
    if jdf is None or jdf.empty:
        print("No journal to backfill from.")
        return
    # closed only
    if "status" in jdf.columns:
        jdf = jdf[jdf["status"].astype(str).str.lower() == "closed"].copy()
    if jdf.empty:
        print("No closed trades to backfill.")
        return

    mdf = _read_csv(ML_LOG_FILE)
    existing_ids = set()
    if mdf is not None and not mdf.empty and "id" in mdf.columns:
        existing_ids = set(mdf["id"].dropna().astype(str))

    # normalize columns that journal may lack
    for col in ["atr","adx","rsi","macd","ema_ratio","strategy","duration_sec","ml_exit_reason","ml_confidence","ml_expected_pnl"]:
        if col not in jdf.columns:
            jdf[col] = 0

    _ensure_ml_headers(ML_LOG_FILE)
    added = 0

    with open(ML_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ML_HEADERS, extrasaction="ignore")

        for _, r in jdf.iterrows():
            tid = str(r.get("trade_id","")).strip()
            if not tid or tid in existing_ids:
                continue

            exit_reason = str(r.get("exit_reason",""))
            is_partial = 1 if "partial" in exit_reason.lower() else 0
            try:
                entry = float(r.get("entry_price", 0))
                exitp = float(r.get("exit_price", 0))
                pnl   = float(r.get("pnl", 0))
            except Exception:
                entry, exitp, pnl = 0.0, 0.0, 0.0

            row = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "id": tid,
                "symbol": r.get("symbol",""),
                "side": r.get("side",""),
                "entry_price": entry,
                "exit_price": exitp,
                "exit_reason": exit_reason,
                "sl": "",
                "tp1": "",
                "tp2": "",
                "tp3": "",
                "atr": float(r.get("atr",0) or 0),
                "trend_strength": 0.0,              # not stored in journal historically
                "volatility": 0.0,                  # not stored in journal historically
                "adx": float(r.get("adx",0) or 0),
                "rsi": float(r.get("rsi",0) or 0),
                "macd": float(r.get("macd",0) or 0),
                "ema_ratio": float(r.get("ema_ratio",1) or 1),
                "pnl_pct": pnl,                     # journal PnL is already percent
                "raw_profit": 0.0,
                "duration_sec": int(r.get("duration_sec",0) or 0),
                "strategy": r.get("strategy",""),
                "leverage": 1,
                "is_partial": is_partial
            }
            w.writerow(row)
            added += 1

    print(f"Backfill complete. Added {added} missing ML rows.")

if __name__ == "__main__":
    main()
