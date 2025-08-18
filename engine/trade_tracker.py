# engine/trade_tracker.py
# Changes:
# - New helper finalize_close() (used internally only; no renames).
# - Persist open positions on open/partial/close via open_positions_store.
# - Save an hourly heartbeat still works as before.

import os
import time
from config import BALANCE_LOG_PATH
from logger.balance_tracker import load_last_balance, update_balance
from logger.journal_writer import update_journal
from logger.trade_logger import log_trade, log_exit
from utils.ml_logger import log_ml_features
from utils.pnl_utils import calc_realistic_pnl
from utils.terminal_logger import tlog
from logger.open_positions_store import load_open_positions, save_open_positions, upsert_position, remove_position

_HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(BALANCE_LOG_PATH)), ".last_heartbeat")

def _should_write_heartbeat(period_sec=3600) -> bool:
    try:
        if not os.path.exists(_HEARTBEAT_FILE):
            return True
        mtime = os.path.getmtime(_HEARTBEAT_FILE)
        return (time.time() - mtime) >= period_sec
    except Exception:
        return True

def _mark_heartbeat_written():
    try:
        os.makedirs(os.path.dirname(_HEARTBEAT_FILE), exist_ok=True)
        with open(_HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception as e:
        tlog(f"⚠️ Heartbeat mark error: {e}")

def finalize_close(trade: dict, atr: float = 0.0):
    """One place to do the close -> logs/journal/ml/balance updates."""
    pnl_pct = calc_realistic_pnl(trade.get("entry_price"), trade.get("exit_price"), trade.get("side","LONG"), trade.get("leverage",1))
    tp_hits = ",".join([f"TP{i+1}" for i in trade.get("hit",[])]) if trade.get("hit") else ""
    log_exit(trade, pnl_pct, tp_hits)
    update_journal(trade)
    log_ml_features(trade, trade.get("trend_strength",0), trade.get("volatility",0), atr)
    update_balance(load_last_balance())
    # remove from persisted store
    remove_position(trade.get("trade_id",""))

def maybe_open_new_trade(open_trades: list, trade: dict):
    """
    Append a freshly created trade to the open list and log it.
    """
    open_trades.append(trade)
    log_trade(trade)
    # persist
    try:
        upsert_position(trade, open_trades)
    except Exception as e:
        tlog(f"⚠️ persist open trade failed: {e}")

def check_open_trades(open_trades: list, symbol_candle_map: dict, atr_map: dict):
    """
    Iterate and update open trades by symbol candle; close and log if needed.
    """
    just_closed = []

    for trade in list(open_trades):
        sym = trade["symbol"]
        candle = symbol_candle_map.get(sym)
        atr = atr_map.get(sym, 0.0)
        if not candle: 
            continue

        from engine.position_model import update_position_status
        old_status = trade["status"]
        trade = update_position_status(trade, candle, atr)

        # Persist any state changes on partial TP (still open)
        if trade.get("hit") and old_status == "open" and trade["status"] == "open":
            update_balance(load_last_balance())  # snapshot
            try:
                upsert_position(trade, open_trades)
            except Exception as e:
                tlog(f"⚠️ persist partial update failed: {e}")

        if trade["status"] == "closed" and old_status != "closed":
            try:
                finalize_close(trade, atr)
            finally:
                just_closed.append(trade)
                try:
                    open_trades.remove(trade)
                except ValueError:
                    pass

    # Ensure persistence after cycle
    try:
        save_open_positions(open_trades)
    except Exception as e:
        tlog(f"⚠️ save_open_positions failed at cycle end: {e}")

    # Heartbeat as before
    if _should_write_heartbeat(3600):
        update_balance(load_last_balance())
        _mark_heartbeat_written()

    return just_closed
