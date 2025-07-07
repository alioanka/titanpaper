# engine/position_model.py

import time
import uuid
from config import TP_MULTIPLIERS, SL_MULTIPLIER, TRAILING_START_AFTER_TP, TRAILING_GAP_ATR
from logger.journal_writer import update_journal
from logger.balance_tracker import update_balance

def build_fake_trade(signal, candle, atr):
    entry = candle["close"]
    side = signal["direction"]
    is_long = side == "LONG"

    if atr is None or atr <= 0 or not isinstance(entry, (int, float)):
        print(f"⚠️ Invalid ATR or entry for {signal['symbol']} — skipping trade")
        return None

    # === Parameters
    MIN_SPREAD_PCT = 0.002  # 0.2%
    min_atr = entry * 0.0015  # 0.15% minimum
    atr = max(atr, min_atr)


    # SL and TP Levels
    sl = entry - atr * SL_MULTIPLIER if is_long else entry + atr * SL_MULTIPLIER
    tp_levels = [
        entry + atr * mult if is_long else entry - atr * mult
        for mult in TP_MULTIPLIERS
    ]

    # === Enforce minimum TP1 spread (in case ATR is very low)
    min_tp_distance = entry * MIN_SPREAD_PCT
    actual_tp1_distance = abs(tp_levels[0] - entry)

    if actual_tp1_distance < min_tp_distance:
        scale = min_tp_distance / actual_tp1_distance
        tp_levels = [entry + (tp - entry) * scale for tp in tp_levels]
        sl = entry - (entry - sl) * scale if is_long else entry + (sl - entry) * scale

    print(f"📊 {signal['symbol']} trade setup → SL: {sl:.2f}, TP1: {tp_levels[0]:.2f}, TP2: {tp_levels[1]:.2f}, TP3: {tp_levels[2]:.2f}")

    if not isinstance(sl, (int, float)) or any(not isinstance(tp, (int, float)) for tp in tp_levels):
        print(f"⚠️ Invalid SL/TP setup for {signal['symbol']}")
        return None

    return {
        "trade_id": str(uuid.uuid4())[:8],
        "symbol": signal["symbol"],
        "side": side,
        "entry_time": time.time(),
        "entry_price": entry,
        "leverage": 1,
        "sl": sl,
        "tp": tp_levels,
        "trailing": {
            "enabled": False,
            "triggered": False,
            "sl": None,
            "sl_gap": atr * TRAILING_GAP_ATR
        },
        "status": "open",
        "hit": [],
        "pnl": 0.0,
        "exit_reason": "",
        "trend_strength": signal.get("trend_strength", 0),
        "volatility": signal.get("volatility", 0),
        "atr": atr,
        "strategy": signal.get("strategy", "unknown")
    }





def update_position_status(trade, candle):
    high = candle["high"]
    low = candle["low"]
    close = candle["close"]
    side = trade["side"]
    is_long = side == "LONG"

    if trade["status"] != "open":
        return trade

    if "tp" not in trade or not isinstance(trade["tp"], list) or len(trade["tp"]) < 3:
        print(f"⚠️ Invalid TP structure: {trade}")
        trade["status"] = "closed"
        trade["exit_reason"] = "error"
        update_journal(trade)
        return trade

    # === SL HIT
    sl_hit = (is_long and low <= trade["sl"]) or (not is_long and high >= trade["sl"])
    if sl_hit:
        trade["exit_price"] = trade["sl"]
        trade["status"] = "closed"
        trade["exit_reason"] = "SL"
        trade["closed_time"] = time.time()
        update_journal(trade)
        return trade

    # === TP Hits
    for i, tp in enumerate(trade["tp"]):
        if i in trade["hit"]:
            continue

        tp_hit = (is_long and high >= tp) or (not is_long and low <= tp)
        if tp_hit:
            trade["hit"].append(i)
            print(f"🎯 TP{i+1} hit: {trade['symbol']} {side} @ {tp:.2f}")

            # TP3 closes the trade
            if i == 2:
                trade["exit_price"] = tp
                trade["status"] = "closed"
                trade["exit_reason"] = "TP3"
                trade["closed_time"] = time.time()
                update_journal(trade)
                return trade

            # Enable trailing SL after any TP
            if not trade["trailing"]["enabled"]:
                trade["trailing"]["enabled"] = True
                print(f"🔁 Trailing SL activated for {trade['symbol']} after TP{i+1}")

            # Log fake exit for ML purposes only
            fake_trade = trade.copy()
            fake_trade["exit_price"] = tp
            fake_trade["exit_reason"] = f"TP{i+1}-Partial"
            from utils.ml_logger import log_ml_features
            log_ml_features(fake_trade, trade.get("trend_strength", 0), trade.get("volatility", 0), trade.get("atr", 0))


            # Log journal and ML on TP1/TP2
            update_journal(trade)
            from utils.ml_logger import log_ml_features
            log_ml_features(trade, trade.get("trend_strength", 0), trade.get("volatility", 0), trade.get("atr", 0))
            return trade  # stay open

    # === Trailing SL Logic
    if trade["trailing"]["enabled"]:
        trail = trade["trailing"]

        if not trail["triggered"]:
            trail["triggered"] = True
            trail["sl"] = close - trail["sl_gap"] if is_long else close + trail["sl_gap"]
            print(f"🟢 Trailing SL initialized for {trade['symbol']} @ {trail['sl']:.4f}")

        new_sl = close - trail["sl_gap"] if is_long else close + trail["sl_gap"]
        if (is_long and new_sl > trail["sl"]) or (not is_long and new_sl < trail["sl"]):
            trail["sl"] = new_sl
            print(f"🔄 Trailing SL moved to {trail['sl']:.4f} for {trade['symbol']}")

        trailing_hit = (is_long and low <= trail["sl"]) or (not is_long and high >= trail["sl"])
        if trailing_hit:
            trade["exit_price"] = trail["sl"]
            trade["status"] = "closed"
            trade["exit_reason"] = "TP1–2" if len(trade.get("hit", [])) in [1, 2] else "TrailingSL"

            trade["closed_time"] = time.time()
            print(f"📌 Trailing SL hit for {trade['symbol']} @ {trail['sl']:.4f}")
            update_journal(trade)
            return trade

    return trade







