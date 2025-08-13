# engine/trade_tracker.py

import os
import time
from config import *
from core.indicator_utils import fetch_recent_candles, calculate_atr
from engine.position_model import build_fake_trade, update_position_status
from logger.trade_logger import log_exit
from logger.journal_writer import update_journal
from logger.balance_tracker import load_last_balance, update_balance
from utils.pnl_utils import calc_realistic_pnl
from utils.ml_logger import log_ml_features

# Heartbeat marker sits next to balance_history.csv
_HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(BALANCE_LOG_PATH)), ".last_heartbeat")

def _should_write_heartbeat(interval_seconds: int = 3600) -> bool:
    now = time.time()
    try:
        if os.path.exists(_HEARTBEAT_FILE):
            with open(_HEARTBEAT_FILE, "r", encoding="utf-8") as f:
                last = float(f.read().strip())
            if now - last < interval_seconds:
                return False
        return True
    except Exception:
        return True  # be permissive if marker is unreadable

def _mark_heartbeat_written():
    try:
        os.makedirs(os.path.dirname(_HEARTBEAT_FILE), exist_ok=True)
        with open(_HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception:
        pass

def maybe_open_new_trade(signal, candle, open_trades, fallback_atr=0.0):
    symbol = signal["symbol"]
    if any(t["symbol"] == symbol and t["status"] == "open" for t in open_trades):
        return None

    df = fetch_recent_candles(symbol)
    if df is None:
        return None

    atr = calculate_atr(df)
    if not atr or atr == 0:
        atr = fallback_atr
        if not atr or atr == 0:
            return None

    trade = build_fake_trade(signal, candle, atr)
    if not trade:
        return None

    return trade

def check_open_trades(open_trades, current_candle):
    still_open = []
    just_closed = []

    for trade in open_trades:
        updated = update_position_status(trade, current_candle)

        # Partial TP balance credit (unchanged logic)
        num_hits = len(updated.get("hit", []))
        if num_hits > 0 and "partial_credit" not in updated and updated["status"] != "closed":
            partial_pct = 0.33 * num_hits  # TP1 = 33%, TP1+TP2 = 66%
            updated["partial_credit"] = True

            pnl_pct = calc_realistic_pnl(
                updated.get("entry_price"),
                updated["tp"][updated["hit"][-1]],
                updated.get("side"),
                updated.get("leverage", 1)
            )

            last_balance = load_last_balance()
            risk_amount = last_balance * RISK_PER_TRADE
            gain = risk_amount * pnl_pct / 100 * partial_pct
            new_balance = last_balance + gain
            update_balance(new_balance)

        # Final closure (unchanged)
        if updated["status"] == "closed":
            last_balance = load_last_balance()
            pnl_pct = calc_realistic_pnl(
                updated.get("entry_price"),
                updated.get("exit_price"),
                updated.get("side"),
                updated.get("leverage", 1)
            )
            updated["pnl"] = pnl_pct

            risk_amount = last_balance * RISK_PER_TRADE
            profit_or_loss = risk_amount * pnl_pct / 100
            new_balance = last_balance + profit_or_loss
            update_balance(new_balance)

            update_journal(updated)
            log_exit(updated)
            log_ml_features(
                updated,
                updated.get("trend_strength", 0),
                updated.get("volatility", 0),
                updated.get("atr", 0),
            )
            just_closed.append(updated["symbol"])
        else:
            still_open.append(updated)

    # ✅ Hourly heartbeat so balance_history.csv grows even on quiet/partial periods
    try:
        if _should_write_heartbeat(3600):
            update_balance(load_last_balance())
            _mark_heartbeat_written()
    except Exception:
        # Best effort; never break trading loop
        pass

    return still_open, just_closed
