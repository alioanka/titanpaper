# validate_logs.py
import os
import pandas as pd
from datetime import datetime, timedelta
from config import JOURNAL_PATH, TRADE_LOG_PATH, BALANCE_LOG_PATH
ML_LOG_PATH = "ml_log.csv"

def _exists(p): return os.path.exists(p) and os.path.getsize(p) > 0
def _read(p): 
    try: return pd.read_csv(p, encoding="utf-8")
    except Exception: return None

def main():
    report = []
    def add(x): 
        print(x); report.append(x)

    add("=== TitanBot-Paper Log Validation ===")

    # JOURNAL
    if _exists(JOURNAL_PATH):
        jdf = _read(JOURNAL_PATH)
        if jdf is None or jdf.empty:
            add("[JOURNAL] EMPTY or unreadable.")
        else:
            need = {"timestamp","trade_id","symbol","side","entry_price","exit_price","status","exit_reason","pnl"}
            missing = need - set(jdf.columns)
            add(f"[JOURNAL] rows={len(jdf)} missing={missing}")
            closed = jdf[jdf["status"].astype(str).str.lower()=="closed"] if "status" in jdf.columns else jdf
            add(f"[JOURNAL] closed_rows={len(closed)}")
            if "pnl" in jdf.columns:
                pnl = pd.to_numeric(jdf["pnl"], errors="coerce").fillna(0)
                bad = pnl.abs() > 20
                add(f"[JOURNAL] |pnl|>20% rows={int(bad.sum())}")
            if "exit_reason" in jdf.columns:
                er = jdf["exit_reason"].astype(str).str.lower()
                if (er=="sl").sum()==0:
                    add("[JOURNAL] ⚠️ No SL detected in entire journal.")
    else:
        add(f"[JOURNAL] MISSING: {JOURNAL_PATH}")
        jdf = None

    # TRADE LOG
    if _exists(TRADE_LOG_PATH):
        tdf = _read(TRADE_LOG_PATH)
        add(f"[TRADE_LOG] rows={0 if tdf is None else len(tdf)}")
    else:
        add(f"[TRADE_LOG] MISSING: {TRADE_LOG_PATH}")

    # ML LOG
    if _exists(ML_LOG_PATH):
        mdf = _read(ML_LOG_PATH)
        if mdf is None or mdf.empty:
            add("[ML_LOG] EMPTY or unreadable.")
        else:
            add(f"[ML_LOG] rows={len(mdf)} cols={list(mdf.columns)}")
            # alignment with journal closed trades
            if jdf is not None and "trade_id" in jdf.columns and "id" in mdf.columns:
                closed_ids = set(jdf[jdf["status"].astype(str).str.lower()=="closed"]["trade_id"].dropna().astype(str))
                ml_ids = set(mdf["id"].dropna().astype(str))
                missing = closed_ids - ml_ids
                add(f"[ALIGN] Closed trades missing in ML log: {len(missing)}")
                if missing:
                    add("  sample: " + ", ".join(list(missing)[:10]))
    else:
        add(f"[ML_LOG] MISSING: {ML_LOG_PATH}")

    # BALANCE
    if _exists(BALANCE_LOG_PATH):
        bdf = _read(BALANCE_LOG_PATH)
        if bdf is not None and not bdf.empty:
            add(f"[BALANCE] rows={len(bdf)} last={bdf.tail(1).to_dict('records')[0]}")
        else:
            add("[BALANCE] EMPTY or unreadable.")
    else:
        add(f"[BALANCE] MISSING: {BALANCE_LOG_PATH}")

    add("=== Validation complete ===")

if __name__ == "__main__":
    main()
