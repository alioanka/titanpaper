# engine/trade_tracker.py

from config import *
from core.indicator_utils import fetch_recent_candles, calculate_atr
from engine.position_model import build_fake_trade, update_position_status
from logger.trade_logger import log_exit
from logger.journal_writer import update_journal
from logger.balance_tracker import load_last_balance, update_balance
from utils.pnl_utils import calc_realistic_pnl

def maybe_open_new_trade(signal, candle, open_trades):
    """
    If signal exists and symbol is not already open, simulate a fake trade.
    """
    symbol = signal["symbol"]
    if any(t["symbol"] == symbol and t["status"] == "open" for t in open_trades):
        return None

    df = fetch_recent_candles(symbol)
    if df is None:
        return None

    atr = calculate_atr(df)
    print(f"📐 {symbol} ATR: {atr:.5f}")

    if not atr or atr == 0:
        return None

    trade = build_fake_trade(signal, candle, atr)

    if not trade:
        print(f"❌ Failed to create trade for {symbol}")
        return None
    print(f"📈 Fake trade opened: {trade['symbol']} {trade['side']} @ {trade['entry_price']}")
    return trade


def check_open_trades(open_trades, current_candle):
    """
    Check open trades for SL/TP/trailing and close/log if needed.
    """
    still_open = []
    just_closed = []

    for trade in open_trades:
        updated = update_position_status(trade, current_candle)

        # ✅ Partial TP balance logic
        num_hits = len(updated.get("hit", []))
        if num_hits > 0 and "partial_credit" not in updated and updated["status"] == "open":
            partial_pct = 0.33 * num_hits  # TP1 = +33%, TP1+TP2 = +66%
            updated["partial_credit"] = True  # prevent re-crediting
            from utils.pnl_utils import calc_realistic_pnl
            pnl_pct = calc_realistic_pnl(
                updated.get("entry_price"),
                updated["tp"][updated["hit"][-1]],
                updated.get("side"),
                updated.get("leverage", 1)
            )
            last_balance = load_last_balance()
            gain = last_balance * (pnl_pct * partial_pct)
            new_balance = last_balance + gain
            update_balance(new_balance)
            print(f"💡 Partial TP balance applied ({partial_pct:.0%}): +{gain:.2f} → {new_balance:.2f}")


        if updated["status"] == "closed":
            from utils.ml_logger import log_ml_features

            print(f"🚪 {updated['symbol']} closed due to {updated.get('exit_reason')} @ {updated.get('exit_price')}")

            just_closed.append(updated["symbol"])  # ← track closed symbol

            log_exit(updated)
            update_journal(updated)

            last_balance = load_last_balance()
            pnl_pct = calc_realistic_pnl(
                updated.get("entry_price"),
                updated.get("exit_price"),
                updated.get("side"),
                updated.get("leverage", 1)
            )
            new_balance = last_balance * (1 + pnl_pct)
            update_balance(new_balance)
            print(f"🧠 Logging ML trade: {updated['symbol']} | Reason: {updated['exit_reason']} | PnL: {pnl_pct:+.5f}")

            log_ml_features(updated, updated.get("trend_strength", 0), updated.get("volatility", 0), updated.get("atr", 0))


            print(f"💰 Balance updated: {last_balance:.2f} → {new_balance:.2f} ({pnl_pct:+.2f}%)")
        else:
            still_open.append(updated)

    return still_open, just_closed

