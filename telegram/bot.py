# telegram/bot.py
import os
import time
import pandas as pd
import telebot
from collections import Counter

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BALANCE_LOG_PATH, TRADE_LOG_PATH, JOURNAL_PATH
from logger.balance_tracker import load_last_balance

bot = telebot.TeleBot(TELEGRAM_TOKEN)

COMMANDS_LIST = """
📊 TitanBot-Paper Telegram Commands:
/balance - Show current paper balance
/lasttrade - Show the most recent trade (from trade_log)
/summary - Show today's performance (from journal)
/log - Show last closed trade (trade_log close row)
/journal - Show last journal entry
/rating - Win/loss stats from journal ✅
/journalstats - Win rates and PnL per symbol ✅
"""

def _norm_exit(x: str) -> str:
    s = str(x or "").strip().lower()
    if s in {"tp3","tp_3","takeprofit3"}:
        return "TP3"
    if "tp" in s and "3" not in s:
        return "TP1–2"
    if "trailing" in s:
        return "TrailingSL"
    if s in {"sl","stop","stoploss","stop_loss"}:
        return "SL"
    return "Other"

def _mini_bar(tp3, tp12, sl, trailing, width=20) -> str:
    total = max(1, tp3+tp12+sl+trailing)
    def seg(n): 
        return int(round((n/total)*width))
    g = seg(tp3); y = seg(tp12); r = seg(sl); t = seg(trailing)
    # pad to width
    while g+y+r+t < width:
        y += 1
    return "█"*g + "▓"*y + "░"*t + "▁"*r

@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.reply_to(message, COMMANDS_LIST)

@bot.message_handler(commands=['balance'])
def cmd_balance(message):
    bal = load_last_balance()
    bot.reply_to(message, f"💰 Current paper balance: ${bal:,.2f}")

@bot.message_handler(commands=['lasttrade'])
def cmd_lasttrade(message):
    try:
        if not os.path.exists(TRADE_LOG_PATH):
            bot.reply_to(message, "No trade_log.csv yet.")
            return
        df = pd.read_csv(TRADE_LOG_PATH)
        if df.empty:
            bot.reply_to(message, "No entries in trade_log.csv.")
            return
        row = df.tail(1).to_dict("records")[0]
        bot.reply_to(message, f"📈 Last trade log:\n{row}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ lasttrade error: {e}")

@bot.message_handler(commands=['log'])
def cmd_log(message):
    # last closed row from trade_log
    try:
        if not os.path.exists(TRADE_LOG_PATH):
            bot.reply_to(message, "No trade_log.csv yet.")
            return
        df = pd.read_csv(TRADE_LOG_PATH)
        if "status" in df.columns:
            closed = df[df["status"].astype(str).str.lower()=="closed"]
        else:
            closed = df
        if closed.empty:
            bot.reply_to(message, "No closed trades yet.")
            return
        row = closed.tail(1).to_dict("records")[0]
        bot.reply_to(message, f"🧾 Trade log (last closed):\n{row}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ log error: {e}")

@bot.message_handler(commands=['journal'])
def cmd_journal(message):
    try:
        if not os.path.exists(JOURNAL_PATH):
            bot.reply_to(message, "No journal.csv yet.")
            return
        df = pd.read_csv(JOURNAL_PATH)
        if df.empty:
            bot.reply_to(message, "Journal empty.")
            return
        row = df.tail(1).to_dict("records")[0]
        bot.reply_to(message, f"📘 Journal (last):\n{row}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ journal error: {e}")

@bot.message_handler(commands=['summary'])
def cmd_summary(message):
    try:
        today_str = time.strftime("%Y-%m-%d")
        if not os.path.exists(JOURNAL_PATH):
            bot.reply_to(message, f"📊 No journal yet for {today_str}.")
            return
        df = pd.read_csv(JOURNAL_PATH)
        if df.empty:
            bot.reply_to(message, f"📊 No closed trades yet for {today_str}.")
            return
        # Filter by today (timestamp starts with yyyy-mm-dd)
        if "timestamp" in df.columns:
            today = df[df["timestamp"].astype(str).str.startswith(today_str)].copy()
        else:
            today = df.copy()
        if "status" in today.columns:
            today = today[today["status"].astype(str).str.lower()=="closed"].copy()
        if today.empty:
            bot.reply_to(message, f"📊 No closed trades yet for {today_str}.")
            return
        # Required cols
        for col in ["exit_reason","pnl","symbol"]:
            if col not in today.columns:
                raise ValueError(f"Missing '{col}' in journal.csv")
        today["exit_reason_norm"] = today["exit_reason"].apply(_norm_exit)
        today["pnl"] = pd.to_numeric(today["pnl"], errors="coerce").fillna(0.0)

        counts = today["exit_reason_norm"].value_counts()
        tp3 = int(counts.get("TP3",0))
        tp12 = int(counts.get("TP1–2",0))
        sl = int(counts.get("SL",0))
        trailing = int(counts.get("TrailingSL",0))
        total_pnl = round(today["pnl"].sum(), 2)

        bar = _mini_bar(tp3,tp12,sl,trailing, width=20)
        msg = (f"📊 Summary for {today_str}:\n"
               f"🏆 TP3: {tp3} | 🎯 TP1–2: {tp12} | 🪤 TrailingSL: {trailing} | 💥 SL: {sl}\n"
               f"{bar}\n"
               f"📈 Total PnL: {total_pnl}%")
        bot.reply_to(message, msg)
    except Exception as e:
        bot.reply_to(message, f"⚠️ summary error: {e}")

@bot.message_handler(commands=['journalstats'])
def cmd_journalstats(message):
    try:
        if not os.path.exists(JOURNAL_PATH):
            bot.reply_to(message, "No journal.csv yet.")
            return
        df = pd.read_csv(JOURNAL_PATH)
        if "status" in df.columns:
            df = df[df["status"].astype(str).str.lower()=="closed"].copy()
        if df.empty:
            bot.reply_to(message, "No closed trades yet.")
            return
        for col in ["symbol","exit_reason","pnl"]:
            if col not in df.columns:
                raise ValueError(f"Missing '{col}' in journal.csv")
        df["exit_reason_norm"] = df["exit_reason"].apply(_norm_exit)
        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)

        out_lines = ["📘 TitanBot Journal Stats:"]
        for sym, g in df.groupby("symbol"):
            counts = g["exit_reason_norm"].value_counts()
            tp3 = int(counts.get("TP3",0))
            tp12 = int(counts.get("TP1–2",0))
            sl = int(counts.get("SL",0))
            trailing = int(counts.get("TrailingSL",0))
            wins = tp3 + tp12
            total = max(1, len(g))
            win_rate = (wins/total)*100
            avg_pnl = g["pnl"].mean()
            out_lines.append(
                f"\n🔹 {sym} ({len(g)} trades)\n"
                f"  - 🏆 TP3: {tp3}\n"
                f"  - 🎯 TP1–2: {tp12}\n"
                f"  - 🪤 TrailingSL: {trailing}\n"
                f"  - 💥 SL: {sl}\n"
                f"  - ✅ Win Rate: {win_rate:.1f}%\n"
                f"  - 💰 Avg PnL: {avg_pnl:.2f}%"
            )
        bot.reply_to(message, "\n".join(out_lines))
    except Exception as e:
        bot.reply_to(message, f"⚠️ journalstats error: {e}")

@bot.message_handler(commands=['rating'])
def cmd_rating(message):
    # Global stats from journal
    try:
        if not os.path.exists(JOURNAL_PATH):
            bot.reply_to(message, "No journal.csv yet.")
            return
        df = pd.read_csv(JOURNAL_PATH)
        if "status" in df.columns:
            df = df[df["status"].astype(str).str.lower()=="closed"].copy()
        if df.empty:
            bot.reply_to(message, "No closed trades yet.")
            return
        df["exit_reason_norm"] = df["exit_reason"].apply(_norm_exit)
        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)

        counts = df["exit_reason_norm"].value_counts()
        tp3 = int(counts.get("TP3",0))
        tp12 = int(counts.get("TP1–2",0))
        sl = int(counts.get("SL",0))
        trailing = int(counts.get("TrailingSL",0))
        wins = tp3 + tp12
        n = len(df)
        win_rate = (wins/max(1,n))*100
        total_pnl = df["pnl"].sum()

        msg = (f"📊 TitanBot Stats (Last {n} closed trades):\n"
               f"🏆 TP3 Wins: {tp3}\n"
               f"🎯 TP1–2 Wins: {tp12}\n"
               f"🪤 TrailingSL: {trailing}\n"
               f"💥 SL Losses: {sl}\n"
               f"✅ Win Rate: {win_rate:.1f}%\n"
               f"💰 Total PnL: {total_pnl:.2f}%")
        bot.reply_to(message, msg)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Rating error: {e}")

def run_telegram_polling():
    bot.infinity_polling()

def send_startup_notice():
    if TELEGRAM_CHAT_ID:
        bot.send_message(TELEGRAM_CHAT_ID, "🤖 TitanBot-Paper has started.\n" + COMMANDS_LIST)

def send_live_alert(message):
    if TELEGRAM_CHAT_ID:
        bot.send_message(TELEGRAM_CHAT_ID, message)
