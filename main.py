# main.py

import time
import uuid
import pandas as pd
from config import *
from dotenv import load_dotenv
import os
from binance.client import Client
from data.price_feed import get_latest_candle
from core.signal_engine import generate_signal
from engine.trade_tracker import check_open_trades, maybe_open_new_trade
from logger.trade_logger import log_trade
from logger.journal_writer import update_journal
from core.indicator_utils import calculate_atr
from telegram.bot import send_live_alert, send_startup_notice
from threading import Thread

# Load secrets
load_dotenv()
client = Client(api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))

# In-memory store of fake open trades
open_trades = []
recently_closed_symbols = set()
symbol_atr_cache = {}


def get_recent_candles(symbol, interval="5m", limit=100):
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(candles, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df = df[["high", "low", "close"]].astype(float)
        return df
    except Exception as e:
        print(f"❌ Failed to fetch historical candles for {symbol}: {e}")
        return None

def run_bot():
    global open_trades
    symbol_cooldowns = {}
    COOLDOWN_SECONDS = 90

    print(f"🚀 Starting {BOT_NAME} in {MODE.upper()} mode...")
    print("🔄 Sending Telegram startup notice...")
    send_startup_notice()
    print("✅ Telegram startup notice sent. Starting loop...")



    while True:
        recently_closed_symbols.clear()

        for symbol in SYMBOLS:
            try:
                candle = get_latest_candle(symbol, TIMEFRAME)

                if not candle or "open" not in candle:
                    print(f"⚠️ Skipping {symbol}: no valid candle data")
                    continue

                print(f"🧠 {symbol} Candle fetched: O={candle['open']} C={candle['close']} H={candle['high']} L={candle['low']}")

                open_trades, just_closed = check_open_trades(open_trades, candle)

                if not isinstance(open_trades, list):
                    print("🚨 open_trades corrupted, resetting.")
                    open_trades = []

                now = time.time()
                for sym in just_closed:
                    symbol_cooldowns[sym] = now + COOLDOWN_SECONDS

                if symbol in recently_closed_symbols:
                    print(f"⏳ Skipping {symbol} — just closed this symbol")
                    continue

                is_open = any(t['symbol'] == symbol and t['status'] == 'open' for t in open_trades)
                cooldown_expiry = symbol_cooldowns.get(symbol)

                if cooldown_expiry and now < cooldown_expiry:
                    print(f"⏳ {symbol} still in cooldown — skipping new entry.")
                    continue

                if not is_open:
                    signal = generate_signal(symbol, candle)
                    if signal:
                        print(f"✅ TRADE SIGNAL: {symbol} | Side: {signal['direction']} | Trend: {signal['confidence']:.4f} | Price: {candle['close']}")
                        
                        # === ML integration (NEW) ===
                        from ml_predictor import predict_trade

                        df = get_recent_candles(symbol)
                        fallback_atr = symbol_atr_cache.get(symbol, 0.0)
                        atr = calculate_atr(df) if df is not None else fallback_atr
                        symbol_atr_cache[symbol] = atr  # <-- update cache live per run

                        signal_data = {
                            'symbol': symbol,
                            'side': signal['direction'],
                            'entry_price': candle['close'],
                            'atr': atr,
                            'trend_strength': signal['confidence'],
                            'volatility': candle.get('volatility', 0.002),  # optionally improve from price_feed
                            'duration_sec': 0
                        }

                        ml_result = predict_trade(signal_data)
                        print(f"[ML] Prediction: {ml_result['exit_reason']}, Confidence: {ml_result['confidence']:.2%}, Expected PnL: {ml_result['expected_pnl']:.2f}%")

                        # Decide if we should proceed (soft filter)
                        if ml_result['exit_reason'] == 'SL' or ml_result['confidence'] < 0.5:
                            print(f"[ML] Skipping trade due to low confidence or SL prediction.")
                            continue  # Skip to next symbol

                        # === Proceed to open trade ===
                        trade = maybe_open_new_trade(signal, candle, open_trades, fallback_atr=fallback_atr)


                        if trade:
                            trade["strategy"] = signal.get("strategy_name", DEFAULT_STRATEGY_NAME)
                            trade["id"] = str(uuid.uuid4())
                            trade["ml_exit_reason"] = ml_result['exit_reason']
                            trade["ml_confidence"] = ml_result['confidence']
                            trade["ml_expected_pnl"] = ml_result['expected_pnl']
                            open_trades.append(trade)
                            log_trade(trade)
                            alert_message = (
                                f"🚀 {symbol} {signal['direction']} Signal\n"
                                f"ML: {ml_result['exit_reason']} ({ml_result['confidence']:.2%})\n"
                                f"PnL est.: {ml_result['expected_pnl']:.2f}%"
                            )
                            #send_live_alert(alert_message)


                    else:
                        print(f"❌ No valid signal for {symbol}")
                else:
                    print(f"📌 {symbol} already has an open trade.")

            except Exception as e:
                print(f"❌ Error for {symbol}: {e}")

        recently_closed_symbols.update(
            [t['symbol'] for t in open_trades if t.get('status') == 'closed']
        )

        time.sleep(EVALUATION_INTERVAL)


if __name__ == "__main__":
 #   Thread(target=run_telegram_polling, daemon=True).start()
    run_bot()

