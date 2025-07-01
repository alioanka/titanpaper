# engine/trade_tracker.py

from config import *
from core.indicator_utils import fetch_recent_candles, calculate_atr
from engine.position_model import build_fake_trade, update_position_status
from logger.trade_logger import log_exit
from logger.journal_writer import update_journal
from logger.balance_tracker import load_last_balance, update_balance
from logger.journal_writer import calc_fake_pnl

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

        if updated["status"] == "closed":
            print(f"🚪 {updated['symbol']} closed due to {updated.get('exit_reason')} @ {updated.get('exit_price')}")

            just_closed.append(updated["symbol"])  # ← track closed symbol

            log_exit(updated)
            update_journal(updated)

            last_balance = load_last_balance()
            pnl_pct = calc_fake_pnl(updated)
            new_balance = last_balance * (1 + pnl_pct)
            update_balance(new_balance)

            print(f"💰 Balance updated: {last_balance:.2f} → {new_balance:.2f} ({pnl_pct:+.2f}%)")
        else:
            still_open.append(updated)

    return still_open, just_closed

