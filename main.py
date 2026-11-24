import os
import requests
from flask import Flask

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=data, timeout=10)
        print("Telegram reply:", r.text)
    except Exception as e:
        print("Error:", e)

@app.route("/")
def home():
    return "Bot is live!"

send_telegram("✅ Colony Bot is ONLINE! Telegram connection is working.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
