# engine/position_model.py
import uuid
from config import TP_MULTIPLIERS, SL_MULTIPLIER, TRAILING_START_AFTER_TP, TRAILING_GAP_ATR, PRICE_BUFFER_PCT
from utils.terminal_logger import tlog
import time

def build_fake_trade(signal: dict, candle: dict, atr: float) -> dict:
    """
    Build an in-memory trade object for paper sim.
    """
    entry = float(candle["close"])
    side = signal["direction"]
    is_long = side.upper() == "LONG"

    if not atr or atr <= 0:
        raise ValueError("ATR must be positive for TP/SL construction.")

    tp1 = entry + (TP_MULTIPLIERS[0]*atr if is_long else -TP_MULTIPLIERS[0]*atr)
    tp2 = entry + (TP_MULTIPLIERS[1]*atr if is_long else -TP_MULTIPLIERS[1]*atr)
    tp3 = entry + (TP_MULTIPLIERS[2]*atr if is_long else -TP_MULTIPLIERS[2]*atr)
    sl  = entry - (SL_MULTIPLIER*atr if is_long else -SL_MULTIPLIER*atr)

    trade = {
        "trade_id": uuid.uuid4().hex[:8],
        "symbol": signal["symbol"],
        "side": side,
        "entry_price": entry,
        "exit_price": None,
        "sl": round(sl,6),
        "tp1": round(tp1,6),
        "tp2": round(tp2,6),
        "tp3": round(tp3,6),
        "status": "open",
        "exit_reason": "",
        "hit": [],                # indices [0,1,2] to show TP hits
        "trail_active": False,
        "trail_level": None,
        "leverage": signal.get("leverage",1),
        "strategy": signal.get("strategy_name","basic_trend"),
        "duration_sec": 0,
        "opened_at": time.strftime("%Y-%m-%d %H:%M:%S"),  # ✅ added (used for catch-up & bookkeeping)
        # pass-through fields for logging/ML if present
        "adx": signal.get("adx",0),
        "rsi": signal.get("rsi",0),
        "macd": signal.get("macd",0),
        "ema_ratio": signal.get("ema_ratio",1.0),
    }
    tlog(f"🧩 Open {trade['symbol']} {side} @ {entry:.4f} | SL {sl:.4f} | TP {tp1:.4f}/{tp2:.4f}/{tp3:.4f}")
    return trade

def _price_hit(level: float, high: float, low: float, is_long: bool) -> bool:
    buf = PRICE_BUFFER_PCT
    if is_long:
        return high >= level*(1 - buf)
    else:
        return low  <= level*(1 + buf)

def update_position_status(trade: dict, candle: dict, atr: float=None) -> dict:
    """
    Update a single open trade with the given candle (same symbol).
    Applies TP/SL logic with buffers and trailing.
    """
    if str(trade.get("status","")).lower() != "open":
        return trade

    high = float(candle["high"])
    low  = float(candle["low"])
    is_long = str(trade["side"]).upper() == "LONG"

    # 1) Check SL first (hard stop)
    if _price_hit(trade["sl"], high, low, not is_long):  # invert direction for SL test
        trade["exit_price"] = trade["sl"]
        trade["status"] = "closed"
        trade["exit_reason"] = "SL"
        tlog(f"🛑 SL hit: {trade['symbol']} {trade['side']} @ {trade['sl']:.4f} | Candle H/L {high:.4f}/{low:.4f}")
        return trade

    # 2) Check TPs in order
    for i, level_key in enumerate(["tp1","tp2","tp3"]):
        if i in trade["hit"]:
            continue
        level = float(trade[level_key])
        if _price_hit(level, high, low, is_long):
            trade["hit"].append(i)
            tlog(f"🎯 {level_key.upper()} hit: {trade['symbol']} {trade['side']} @ {level:.4f} | H/L {high:.4f}/{low:.4f}")
            # trailing activation after TP2
            if i+1 >= TRAILING_START_AFTER_TP and atr and atr>0:
                gap = TRAILING_GAP_ATR*float(atr)
                trail = (level - gap) if is_long else (level + gap)
                prev = trade.get("trail_level")
                trade["trail_active"] = True
                trade["trail_level"]  = max(prev, trail) if prev and is_long else (min(prev, trail) if prev and not is_long else trail)
                tlog(f"🪢 Trailing set @ {trade['trail_level']:.4f} (gap≈{TRAILING_GAP_ATR}×ATR)")
            # if TP3: close
            if i == 2:
                trade["exit_price"] = level
                trade["status"] = "closed"
                trade["exit_reason"] = "TP3"
                return trade
            # do not return; allow multiple TP hits same candle

    # 3) Trailing SL if active
    if trade.get("trail_active") and atr and atr>0:
        tl = float(trade["trail_level"])
        # Trail moves only in favorable direction
        if is_long:
            # Raise trail if price made a new high beyond TP2 area
            new_trail = high - TRAILING_GAP_ATR*float(atr)
            if new_trail > tl:
                trade["trail_level"] = new_trail
            # Triggered?
            if low <= trade["trail_level"]*(1 + PRICE_BUFFER_PCT):
                trade["exit_price"] = trade["trail_level"]
                trade["status"] = "closed"
                trade["exit_reason"] = "TrailingSL"
                tlog(f"🪤 TrailingSL close @ {trade['trail_level']:.4f} | H/L {high:.4f}/{low:.4f}")
        else:
            new_trail = low + TRAILING_GAP_ATR*float(atr)
            if new_trail < tl:
                trade["trail_level"] = new_trail
            if high >= trade["trail_level"]*(1 - PRICE_BUFFER_PCT):
                trade["exit_price"] = trade["trail_level"]
                trade["status"] = "closed"
                trade["exit_reason"] = "TrailingSL"
                tlog(f"🪤 TrailingSL close @ {trade['trail_level']:.4f} | H/L {high:.4f}/{low:.4f}")

    return trade
