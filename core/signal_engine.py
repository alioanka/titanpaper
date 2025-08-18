# core/signal_engine.py
from config import MIN_TREND_STRENGTH, MIN_VOLATILITY

def generate_signal(symbol, candle):
    """
    Decide whether to open a fake LONG or SHORT based on simple trend + volatility logic.
    """
    close = float(candle["close"])
    open_ = float(candle["open"])
    high  = float(candle["high"])
    low   = float(candle["low"])

    trend_strength = (close - open_) / max(open_, 1e-9)
    volatility = (high - low) / max(open_, 1e-9)

    if abs(trend_strength) < MIN_TREND_STRENGTH or volatility < MIN_VOLATILITY:
        return None

    direction = "LONG" if trend_strength > 0 else "SHORT"
    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": abs(trend_strength),
        "strategy_name": "basic_trend"
    }
