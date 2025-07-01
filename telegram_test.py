import requests

TELEGRAM_TOKEN = "7678357905:AAEe0MfHa4ZYhFnDhlUPL2oDaNXSoLo-YaM"
CHAT_ID = "462007586"

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
data = {
    "chat_id": CHAT_ID,
    "text": "✅ Telegram test from VPS"
}

response = requests.post(url, data=data)
print(response.status_code, response.text)
