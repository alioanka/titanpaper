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

    # ✅ Sanity check
    if atr is None or atr <= 0 or not isinstance(entry, (int, float)):
        print(f"⚠️ Invalid ATR or entry for {signal['symbol']} — skipping trade")
        return None

    # === Parameters
    MIN_SPREAD_PCT = 0.002  # 0.2%

    # SL and TP Levels
    sl = entry - atr * SL_MULTIPLIER if is_long else entry + atr * SL_MULTIPLIER
    tp_levels = [
        entry + atr * mult if is_long else entry - atr * mult
        for mult in TP_MULTIPLIERS
    ]

    # === Enforce minimum TP1 spread (in case of flat ATR)
    min_tp_distance = entry * MIN_SPREAD_PCT
    actual_tp1_distance = abs(tp_levels[0] - entry)

    if actual_tp1_distance < min_tp_distance:
        scale = min_tp_distance / actual_tp1_distance
        tp_levels = [entry + (tp - entry) * scale for tp in tp_levels]
        sl = entry - (entry - sl) * scale if is_long else entry + (sl - entry) * scale

    print(f"📊 {signal['symbol']} trade setup → SL: {sl:.2f}, TP1: {tp_levels[0]:.2f}, TP2: {tp_levels[1]:.2f}, TP3: {tp_levels[2]:.2f}")

    # ✅ SL/TP validation
    if not isinstance(sl, (int, float)) or any(not isinstance(tp, (int, float)) for tp in tp_levels):
        print(f"⚠️ Invalid SL/TP setup for {signal['symbol']}")
        return None

    return {
        "trade_id": str(uuid.uuid4())[:8],
        "symbol": signal["symbol"],
        "side": side,
        "entry_time": time.time(),
        "entry_price": entry,
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
        "exit_reason": "",  # ✅ changed from None for consistency
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

    # === SL Hit
    if (is_long and low <= trade["sl"]) or (not is_long and high >= trade["sl"]):
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

        if (is_long and high >= tp) or (not is_long and low <= tp):
            trade["hit"].append(i)
            print(f"🎯 TP{i+1} hit: {trade['symbol']} {side} @ {tp:.2f}")

            if i == 0:
                trade["trailing"]["enabled"] = True
                trade["exit_price"] = tp
                trade["exit_reason"] = "TP1"
                trade["status"] = "closed"
            elif i == 1:
                trade["trailing"]["enabled"] = True
                avg = (trade["tp"][0] + trade["tp"][1]) / 2
                trade["exit_price"] = avg
                trade["exit_reason"] = "TP1-2"
                trade["status"] = "closed"
            elif i == 2:
                trade["exit_price"] = tp
                trade["exit_reason"] = "TP3"
                trade["status"] = "closed"

            trade["closed_time"] = time.time()
            update_journal(trade)
            return trade

    # === Trailing SL logic
    if trade["trailing"]["enabled"]:
        trail = trade["trailing"]
        if not trail["triggered"]:
            trail["triggered"] = True
            trail["sl"] = close - trail["sl_gap"] if is_long else close + trail["sl_gap"]
        else:
            new_sl = close - trail["sl_gap"] if is_long else close + trail["sl_gap"]
            if (is_long and new_sl > trail["sl"]) or (not is_long and new_sl < trail["sl"]):
                trail["sl"] = new_sl

        if (is_long and low <= trail["sl"]) or (not is_long and high >= trail["sl"]):
            trade["exit_price"] = trail["sl"]
            trade["exit_reason"] = "TrailingSL"
            trade["status"] = "closed"
            trade["closed_time"] = time.time()
            update_journal(trade)
            return trade

    return trade





