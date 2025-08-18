# main.py
"""
TitanBot-Paper main loop (paper trading)

Key points:
- Fetch per-symbol latest candle (for entries) and recent candles (for ATR/features)
- Update open trades via check_open_trades() using per-symbol candle/ATR maps
- ML gating: skip if classifier predicts SL or confidence < 0.5 (configurable by editing thresholds)
- Cooldown per symbol after a close
- All logging/writing is fail-closed (writers handle headers/dirs)
"""

import os
import time
import uuid
import pandas as pd
from dotenv import load_dotenv

from config import (
    SYMBOLS,
    TIMEFRAME,
    EVALUATION_INTERVAL,
    COOLDOWN_SECONDS,
    MIN_TREND_STRENGTH,
    MIN_VOLATILITY,
)

from data.price_feed import get_latest_candle
from core.signal_engine import generate_signal
from core.indicator_utils import fetch_recent_candles, calculate_atr
from engine.position_model import build_fake_trade  # construct paper trade object
from engine.trade_tracker import check_open_trades, maybe_open_new_trade
from telegram.bot import send_live_alert, send_startup_notice
from utils.terminal_logger import tlog

# Optional: use ML predictor if available
try:
    from ml_predictor import predict_trade
    _HAS_ML = True
except Exception as _e:
    tlog(f"⚠️ ML predictor unavailable, running without ML gating: {_e}")
    _HAS_ML = False

# Optional: TA feature builder (used for ML features if available)
try:
    from ml.feature_builder import build_features as build_ml_features
    _HAS_FB = True
except Exception as _e:
    tlog(f"⚠️ Feature builder unavailable, ML features limited: {_e}")
    _HAS_FB = False


def _get_features_for_symbol(symbol: str, interval: str = None, limit: int = 100):
    """
    Helper: fetch recent candles and compute indicators for ML.
    Returns (df, last_features_dict, atr_value).
    """
    try:
        df = fetch_recent_candles(symbol, interval=interval or TIMEFRAME, limit=limit)
        if df is None or df.empty:
            return None, None, 0.0

        atr_val = calculate_atr(df, period=14) or 0.0

        # Build ML features if available
        feats = None
        if _HAS_FB:
            try:
                fdf = build_ml_features(df.rename(columns={"open": "open", "high": "high", "low": "low", "close": "close"}))
                if fdf is not None and not fdf.empty:
                    last = fdf.tail(1).to_dict("records")[0]
                    feats = {
                        "atr": float(last.get("atr", 0.0)),
                        "adx": float(last.get("adx", 0.0)),
                        "rsi": float(last.get("rsi", 0.0)),
                        "macd": float(last.get("macd", 0.0)),
                        "ema_ratio": float(last.get("ema_ratio", 1.0)),
                        "volatility": float(last.get("volatility", 0.0)),
                    }
            except Exception as e:
                tlog(f"⚠️ Feature build error for {symbol}: {e}")
                feats = None

        return df, feats, atr_val
    except Exception as e:
        tlog(f"❌ _get_features_for_symbol error [{symbol}]: {e}")
        return None, None, 0.0


def run_bot():
    load_dotenv()

    tlog("🚀 TitanBot-Paper starting…")
    try:
        send_startup_notice()
    except Exception as e:
        tlog(f"⚠️ Telegram startup notice failed (continuing): {e}")

    open_trades = []                 # list of trade dicts (status=open/closed)
    symbol_cooldowns = {}            # {symbol: epoch_until}
    symbol_atr_cache = {}            # {symbol: last_atr_val}

    while True:
        cycle_start = time.time()
        symbol_candle_map = {}       # {symbol: latest candle dict}
        atr_map = {}                 # {symbol: atr}

        # 1) Fetch latest candle (for entries) + recent candles (for ATR/features)
        for symbol in SYMBOLS:
            try:
                candle = get_latest_candle(symbol, TIMEFRAME)
                if not candle or "open" not in candle:
                    tlog(f"⚠️ Skipping {symbol}: no valid candle data")
                    continue

                # Normalize types
                candle = {
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "volume": float(candle.get("volume", 0.0)),
                    "volatility": float(candle.get("volatility", 0.0)),
                }
                symbol_candle_map[symbol] = candle

                # Pull recent candles for ATR/features once per cycle
                _, feats, atr_val = _get_features_for_symbol(symbol, interval=TIMEFRAME, limit=100)
                if atr_val and atr_val > 0:
                    atr_map[symbol] = atr_val
                    symbol_atr_cache[symbol] = atr_val
                else:
                    # If ATR fails for this cycle, fall back to last cache
                    atr_map[symbol] = symbol_atr_cache.get(symbol, 0.0)

                # Log the candle snapshot for visibility
                tlog(f"🧠 {symbol} Candle: O={candle['open']} C={candle['close']} H={candle['high']} L={candle['low']} | ATR≈{atr_map[symbol]}")

            except Exception as e:
                tlog(f"❌ Candle/ATR fetch error for {symbol}: {e}")

        # 2) Update open trades against *their own* symbol candle and ATR
        try:
            just_closed = check_open_trades(open_trades, symbol_candle_map, atr_map)
        except Exception as e:
            tlog(f"❌ check_open_trades error: {e}")
            just_closed = []

        # Apply cooldowns for just-closed symbols
        now = time.time()
        for tr in just_closed:
            sym = tr.get("symbol")
            if sym:
                symbol_cooldowns[sym] = now + COOLDOWN_SECONDS

        # 3) Entry: evaluate each symbol if it has no open trade and not cooling down
        for symbol in SYMBOLS:
            try:
                # Skip if candle not present this cycle
                candle = symbol_candle_map.get(symbol)
                if not candle:
                    continue

                # Skip if we just closed or cooling
                if symbol in symbol_cooldowns:
                    if now < symbol_cooldowns[symbol]:
                        tlog(f"⏳ {symbol} still in cooldown — skipping new entry.")
                        continue
                    else:
                        symbol_cooldowns.pop(symbol, None)

                # Skip if already has an open trade
                has_open = any(t["symbol"] == symbol and str(t.get("status","")).lower() == "open" for t in open_trades)
                if has_open:
                    tlog(f"📌 {symbol} already has an open trade.")
                    continue

                # Generate baseline signal (trend/vol filters)
                signal = generate_signal(symbol, candle)
                if not signal:
                    tlog(f"❌ No valid signal for {symbol}")
                    continue

                # Build ML feature vector if possible
                feats_df, feats, atr_val = _get_features_for_symbol(symbol, interval=TIMEFRAME, limit=100)
                if atr_val <= 0:
                    # If ATR is zero, skip opening (we need ATR for TP/SL construction)
                    tlog(f"⚠️ ATR invalid for {symbol}, skipping entry.")
                    continue

                # Compose ML input
                ml_features = {
                    "symbol": symbol,
                    "side": signal["direction"],
                    "entry_price": candle["close"],
                    "atr": atr_val,
                    "trend_strength": float(signal.get("confidence", 0.0)),
                    "volatility": float(candle.get("volatility", 0.0)),
                    "duration_sec": 0,
                    "adx": feats.get("adx", 0.0) if feats else 0.0,
                    "rsi": feats.get("rsi", 0.0) if feats else 50.0,
                    "macd": feats.get("macd", 0.0) if feats else 0.0,
                    "ema_ratio": feats.get("ema_ratio", 1.0) if feats else 1.0,
                }

                # ML gating (optional)
                if _HAS_ML:
                    try:
                        ml_result = predict_trade(ml_features)
                        conf = float(ml_result.get("confidence", 0.0))
                        pred_exit = str(ml_result.get("exit_reason",""))
                        exp_pnl = float(ml_result.get("expected_pnl", 0.0))
                        tlog(f"[ML] {symbol} Pred: {pred_exit} | Conf: {conf:.2f} | ExpPnL: {exp_pnl:.2f}%")

                        if pred_exit.upper() == "SL" or conf < 0.5:
                            tlog(f"[ML] Skipping {symbol} due to low confidence or SL prediction.")
                            continue

                        # Attach ML metadata to the soon-to-open trade (stored in signal)
                        signal["ml_exit_reason"] = pred_exit
                        signal["ml_confidence"] = conf
                        signal["ml_expected_pnl"] = exp_pnl
                    except Exception as e:
                        tlog(f"⚠️ ML gating error (continuing without ML): {e}")

                # Build trade object (includes TPs/SL); attach indicators for logging/ML
                signal["leverage"] = 1  # update if you simulate leverage
                signal["adx"] = ml_features["adx"]
                signal["rsi"] = ml_features["rsi"]
                signal["macd"] = ml_features["macd"]
                signal["ema_ratio"] = ml_features["ema_ratio"]

                trade = build_fake_trade(signal, candle, atr_val)
                # Pass through ML metadata if present
                if "ml_exit_reason" in signal:
                    trade["ml_exit_reason"] = signal["ml_exit_reason"]
                    trade["ml_confidence"] = signal["ml_confidence"]
                    trade["ml_expected_pnl"] = signal["ml_expected_pnl"]

                maybe_open_new_trade(open_trades, trade)

            except Exception as e:
                tlog(f"❌ Entry error for {symbol}: {e}")

        # 4) Sleep until next cycle (respect evaluation interval)
        elapsed = time.time() - cycle_start
        to_sleep = max(1.0, EVALUATION_INTERVAL - elapsed)
        time.sleep(to_sleep)


if __name__ == "__main__":
    run_bot()
