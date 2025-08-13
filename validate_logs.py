# validate_logs.py

import os
from datetime import datetime
import pandas as pd
from config import JOURNAL_PATH, TRADE_LOG_PATH, BALANCE_LOG_PATH

ML_LOG_PATH = "ml_log.csv"  # stays in project root

REPORT_PATH = os.path.join(os.path.dirname(JOURNAL_PATH), "data_quality_log.txt")

def _exists(path): return os.path.exists(path) and os.path.getsize(path) > 0

def _read(path, **kw):
    try:
        return pd.read_csv(path, encoding="utf-8", **kw)
    except Exception:
        return None

def _bucket(reason: str):
    r = (reason or "").upper().replace("–", "-")
    if "TP3" in r: return "tp3"
    if "TP1-2" in r or "TP2" in r or "TP1-PARTIAL" in r or "TP1" in r: return "tp12"
    if r == "SL" or "STOP" in r: return "sl"
    return "other"

def main():
    lines = []
    add = lines.append
    add(f"=== TitanBot Data Quality Report @ {datetime.now():%Y-%m-%d %H:%M:%S} ===")

    # JOURNAL
    if _exists(JOURNAL_PATH):
        jdf = _read(JOURNAL_PATH)
        if jdf is None or jdf.empty:
            add(f"[JOURNAL] ERROR: unreadable or empty: {JOURNAL_PATH}")
            jdf = None
        else:
            add(f"[JOURNAL] OK: {len(jdf)} rows")
            need = ["timestamp","symbol","side","entry_price","exit_price","status","exit_reason","pnl"]
            miss = [c for c in need if c not in jdf.columns]
            if miss: add(f"[JOURNAL] MISSING COLUMNS: {miss}")

            # Closed only
            cdf = jdf
            if "status" in jdf.columns:
                cdf = jdf[jdf["status"].astype(str).str.lower() == "closed"].copy()

            if "pnl" in cdf.columns:
                cdf["pnl"] = pd.to_numeric(cdf["pnl"], errors="coerce").fillna(0.0)
                suspicious = cdf[cdf["pnl"].abs() > 20]  # >20% on 5m is likely off
                add(f"[JOURNAL] Closed trades: {len(cdf)} | Suspicious PnL (>20%): {len(suspicious)}")
                if len(suspicious) > 0:
                    add(suspicious[["timestamp","symbol","exit_reason","pnl"]].tail(10).to_string(index=False))

            if "exit_reason" in cdf.columns and not cdf.empty:
                buckets = cdf["exit_reason"].astype(str).apply(_bucket).value_counts()
                add(f"[JOURNAL] Exit distribution: {buckets.to_dict()}")

                # Heuristic: in a strong uptrend week, TP3 should not be zero
                if buckets.get("tp3", 0) == 0 and buckets.get("tp12", 0) > 10:
                    add("[SUGGESTION] No TP3 detected across many wins. Consider: TRAILING_START_AFTER_TP=2 and TRAILING_GAP_ATR=1.0–1.3 (already set to 1.1). Optionally bring TP3 closer.")
    else:
        add(f"[JOURNAL] MISSING: {JOURNAL_PATH}")
        jdf = None

    # TRADE LOG
    if _exists(TRADE_LOG_PATH):
        tdf = _read(TRADE_LOG_PATH)
        if tdf is None or tdf.empty:
            add(f"[TRADE_LOG] ERROR: unreadable or empty: {TRADE_LOG_PATH}")
        else:
            add(f"[TRADE_LOG] OK: {len(tdf)} rows")
    else:
        add(f"[TRADE_LOG] MISSING: {TRADE_LOG_PATH}")

    # ML LOG
    if _exists(ML_LOG_PATH):
        mdf = _read(ML_LOG_PATH)
        if mdf is None or mdf.empty:
            add(f"[ML_LOG] ERROR: unreadable or empty: {ML_LOG_PATH}")
        else:
            add(f"[ML_LOG] OK: {len(mdf)} rows")
            # Cross-check closed trades present in ML log
            if jdf is not None and "trade_id" in jdf.columns and "status" in jdf.columns and "id" in mdf.columns:
                closed_ids = set(jdf[jdf["status"].astype(str).str.lower()=="closed"]["trade_id"].dropna().astype(str))
                ml_ids = set(mdf["id"].dropna().astype(str))
                missing = closed_ids - ml_ids
                add(f"[ALIGN] Closed trades missing in ML log: {len(missing)}")
                if len(missing) > 0:
                    add("  sample: " + ", ".join(list(missing)[:10]))
    else:
        add(f"[ML_LOG] MISSING: {ML_LOG_PATH}")

    # BALANCE
    if _exists(BALANCE_LOG_PATH):
        bdf = _read(BALANCE_LOG_PATH)
        if bdf is None or bdf.empty:
            add(f"[BALANCE] ERROR: unreadable or empty: {BALANCE_LOG_PATH}")
        else:
            add(f"[BALANCE] OK: {len(bdf)} rows | Latest: {bdf.tail(1).to_dict(orient='records')}")
    else:
        add(f"[BALANCE] MISSING: {BALANCE_LOG_PATH} — expected on next heartbeat/partial/close")

    # Write report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")

    # Console
    print("\n".join(lines))

if __name__ == "__main__":
    main()
