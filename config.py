# config.py

### === GENERAL SETTINGS === ###
BOT_NAME = "TitanBot-Paper"
BASE_CURRENCY = "USDT"
EXCHANGE = "binance"
MODE = "paper"

### === SYMBOLS TO TRACK === ###
SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT"
]

### === STRATEGY SETTINGS === ###
TIMEFRAME = "1m"  # Binance supported intervals: 1m, 3m, 5m, 15m, etc.
MIN_TREND_STRENGTH = 0.0001
MIN_VOLATILITY = 0.0003  # % per candle

### === PAPER TRADING CONFIG === ###
INITIAL_BALANCE = 5000.0
MAX_RISK_PER_TRADE = 0.02  # 2% of balance
TP_MULTIPLIERS = [1.0, 1.5, 2.5]  # Multiple TP levels (based on ATR)
SL_MULTIPLIER = 1.0  # Stop-loss distance (ATR)
TRAILING_START_AFTER_TP = 1  # After TP1, activate trailing
TRAILING_GAP_ATR = 0.5

### === LOGGING === ###
TRADE_LOG_PATH = "logs/trade_log.csv"
JOURNAL_PATH = "logs/journal.csv"
BALANCE_LOG_PATH = "logs/balance_history.csv"

# Telegram Bot Config
TELEGRAM_TOKEN = "7678357905:AAEe0MfHa4ZYhFnDhlUPL2oDaNXSoLo-YaM"
TELEGRAM_CHAT_ID = "462007586"

EVALUATION_INTERVAL = 30
DEFAULT_STRATEGY_NAME = "SmartTrendStrategy"
