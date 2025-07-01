# telegram/bot.py

import os
import time
import csv
import telebot
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BALANCE_LOG_PATH, TRADE_LOG_PATH, JOURNAL_PATH
from logger.balance_tracker import load_last_balance

bot = telebot.TeleBot(TELEGRAM_TOKEN)

COMMANDS_LIST = """
📊 TitanBot-Paper Telegram Commands:
/balance - Show current paper balance
/lasttrade - Show the most recent trade
/summary - Show today's performance summary
/log - Show last closed trade (log)
/journal - Show last journal entry
"""

@bot.message_handler(commands=['start', 'help'])
def help_msg(message):
    bot.send_message(message.chat.id, COMMANDS_LIST)

@bot.message_handler(commands=['balance'])
def balance(message):
    balance = load_last_balance()
    bot.send_message(message.chat.id, f"💰 Current paper balance: ${balance:.2f}")

@bot.message_handler(commands=['lasttrade'])
def last_trade(message):
    if not os.path.exists(TRADE_LOG_PATH):
        bot.send_message(message.chat.id, "No trades yet.")
        return
    with open(TRADE_LOG_PATH, "r") as f:
        lines = f.readlines()
        if len(lines) < 2:
            bot.send_message(message.chat.id, "No trades yet.")
        else:
            bot.send_message(message.chat.id, f"📈 Last trade log:\n{lines[-1]}")

@bot.message_handler(commands=['log'])
def trade_log(message):
    if not os.path.exists(TRADE_LOG_PATH):
        bot.send_message(message.chat.id, "No trade log yet.")
        return
    with open(TRADE_LOG_PATH, "r") as f:
        lines = f.readlines()
        if len(lines) > 1:
            bot.send_message(message.chat.id, f"🧾 Trade log (last closed):\n{lines[-1]}")
        else:
            bot.send_message(message.chat.id, "No closed trades in log yet.")

@bot.message_handler(commands=['journal'])
def journal(message):
    if not os.path.exists(JOURNAL_PATH):
        bot.send_message(message.chat.id, "No journal entries yet.")
        return
    with open(JOURNAL_PATH, "r") as f:
        lines = f.readlines()
        if len(lines) > 1:
            bot.send_message(message.chat.id, f"📘 Journal (last):\n{lines[-1]}")
        else:
            bot.send_message(message.chat.id, "No journal entries yet.")

@bot.message_handler(commands=['summary'])
def summary(message):
    if not os.path.exists(JOURNAL_PATH):
        bot.send_message(message.chat.id, "No journal data to summarize.")
        return

    today = time.strftime("%Y-%m-%d")
    wins, losses, pnl_sum = 0, 0, 0.0

    with open(JOURNAL_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["timestamp"].startswith(today):
                try:
                    pnl = float(row["pnl"])
                    pnl_sum += pnl
                    if pnl > 0:
                        wins += 1
                    elif pnl < 0:
                        losses += 1
                except:
                    continue

    bot.send_message(message.chat.id, f"📊 Today’s Summary ({today}):\nWins: {wins}\nLosses: {losses}\nTotal PnL: {pnl_sum*100:.2f}%")

def run_telegram_polling():
    bot.infinity_polling()

def send_startup_notice():
    bot.send_message(TELEGRAM_CHAT_ID, "🤖 TitanBot-Paper has started.\n" + COMMANDS_LIST)
