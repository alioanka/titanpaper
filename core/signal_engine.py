# core/signal_engine.py

from core.indicator_utils import calculate_atr
from config import MIN_TREND_STRENGTH, MIN_VOLATILITY, SL_MULTIPLIER

def generate_signal(symbol, candle):
    """
    Decide whether to open a fake LONG or SHORT based on simple trend + volatility logic.
    """
    # Use a simplified fake trend indicator (close vs open)
    close = candle["close"]
    open_ = candle["open"]
    trend_strength = (close - open_) / open_

    volatility = (candle["high"] - candle["low"]) / open_

    print(f"🧪 {symbol} - Trend: {trend_strength:.4f}, Volatility: {volatility:.4f}")
    if abs(trend_strength) < MIN_TREND_STRENGTH:
        print(f"❌ Trend too weak for {symbol}")
    if volatility < MIN_VOLATILITY:
        print(f"❌ Volatility too low for {symbol}")
   

    if abs(trend_strength) < MIN_TREND_STRENGTH or volatility < MIN_VOLATILITY:
        return None  # No trade

    direction = "LONG" if trend_strength > 0 else "SHORT"

    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": abs(trend_strength),
        "candle": candle,
        "strategy_name": "basic_trend"
    }
