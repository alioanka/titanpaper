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
from ml.feature_builder import build_features
from utils.terminal_logger import tlog
from engine.position_model import update_position_status

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
        tlog(f"❌ Failed to fetch historical candles for {symbol}: {e}")
        return None

def run_bot():
    global open_trades
    symbol_cooldowns = {}
    COOLDOWN_SECONDS = 90

    tlog(f"🚀 Starting {BOT_NAME} in {MODE.upper()} mode...")
    tlog("🔄 Sending Telegram startup notice...")
    send_startup_notice()
    tlog("✅ Telegram startup notice sent. Starting loop...")

    while True:
        recently_closed_symbols.clear()

        for symbol in SYMBOLS:
            try:
                candle = get_latest_candle(symbol, TIMEFRAME)

                if not candle or "open" not in candle:
                    tlog(f"⚠️ Skipping {symbol}: no valid candle data")
                    continue

                tlog(f"🧠 {symbol} Candle fetched: O={candle['open']} C={candle['close']} H={candle['high']} L={candle['low']}")

                # === Update TP/SL status for existing trades
                for trade in open_trades:
                    if trade["symbol"] == symbol and trade["status"] == "open":
                        old_status = trade["status"]
                        trade = update_position_status(trade, candle)
                        if trade["status"] == "closed" and old_status != "closed":
                            recently_closed_symbols.add(symbol)

                open_trades = [t for t in open_trades if t["status"] == "open"]

                now = time.time()
                for sym in recently_closed_symbols:
                    symbol_cooldowns[sym] = now + COOLDOWN_SECONDS

                if symbol in recently_closed_symbols:
                    tlog(f"⏳ Skipping {symbol} — just closed this symbol")
                    continue

                is_open = any(t['symbol'] == symbol and t['status'] == 'open' for t in open_trades)
                cooldown_expiry = symbol_cooldowns.get(symbol)

                if cooldown_expiry and now < cooldown_expiry:
                    tlog(f"⏳ {symbol} still in cooldown — skipping new entry.")
                    continue

                if not is_open:
                    signal = generate_signal(symbol, candle)
                    if signal:
                        tlog(f"✅ TRADE SIGNAL: {symbol} | Side: {signal['direction']} | Trend: {signal['confidence']:.4f} | Price: {candle['close']}")

                        # === ML integration ===
                        from ml_predictor import predict_trade

                        df = get_recent_candles(symbol)
                        fallback_atr = symbol_atr_cache.get(symbol, 0.0)
                        atr = calculate_atr(df) if df is not None else fallback_atr
                        symbol_atr_cache[symbol] = atr

                        adx, rsi, macd, ema_ratio, volatility = 0.0, 0.0, 0.0, 1.0, 0.002
                        if df is not None and not df.empty:
                            df_indicators = build_features(df)
                            if not df_indicators.empty:
                                adx = df_indicators['adx'].iloc[-1]
                                rsi = df_indicators['rsi'].iloc[-1]
                                macd = df_indicators['macd'].iloc[-1]
                                ema_ratio = df_indicators['ema_ratio'].iloc[-1]
                                volatility = df_indicators['volatility'].iloc[-1]
                            else:
                                tlog(f"⚠️ Indicator DataFrame is empty for {symbol}, skipping.")
                                continue
                        else:
                            tlog(f"⚠️ No candle data for {symbol}, skipping.")
                            continue

                        signal_data = {
                            'symbol': symbol,
                            'side': signal['direction'],
                            'entry_price': candle['close'],
                            'atr': atr,
                            'trend_strength': signal['confidence'],
                            'volatility': volatility,
                            'duration_sec': 0,
                            'adx': adx,
                            'rsi': rsi,
                            'macd': macd,
                            'ema_ratio': ema_ratio
                        }

                        ml_result = predict_trade(signal_data)
                        tlog(f"[ML] Prediction: {ml_result['exit_reason']}, Confidence: {ml_result['confidence']:.2%}, Expected PnL: {ml_result['expected_pnl']:.2f}%")

                        if ml_result['exit_reason'] == 'SL' or ml_result['confidence'] < 0.5:
                            tlog(f"[ML] Skipping trade due to low confidence or SL prediction.")
                            continue

                        trade = maybe_open_new_trade(signal, candle, open_trades, fallback_atr=fallback_atr)

                        if trade:
                            trade["strategy"] = signal.get("strategy_name", DEFAULT_STRATEGY_NAME)
                            trade["id"] = str(uuid.uuid4())
                            trade["ml_exit_reason"] = ml_result['exit_reason']
                            trade["ml_confidence"] = ml_result['confidence']
                            trade["ml_expected_pnl"] = ml_result['expected_pnl']

                            trade["atr"] = atr
                            trade["adx"] = adx
                            trade["rsi"] = rsi
                            trade["macd"] = macd
                            trade["ema_ratio"] = ema_ratio

                            open_trades.append(trade)
                            log_trade(trade)

                            alert_message = (
                                f"🚀 {symbol} {signal['direction']} Signal\n"
                                f"ML: {ml_result['exit_reason']} ({ml_result['confidence']:.2%})\n"
                                f"PnL est.: {ml_result['expected_pnl']:.2f}%"
                            )
                            # send_live_alert(alert_message)

                    else:
                        tlog(f"❌ No valid signal for {symbol}")
                else:
                    tlog(f"📌 {symbol} already has an open trade.")

            except Exception as e:
                tlog(f"❌ Error for {symbol}: {e}")

        recently_closed_symbols.clear()
        time.sleep(EVALUATION_INTERVAL)

if __name__ == "__main__":
    run_bot()
