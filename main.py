from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route("/")
def home():
    return "XAUUSD 15M Bot is Online - Colony"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    price = float(data.get("price", 0))
    action = data.get("action", "BUY")

    if action == "BUY":
        sl = price - 5
        tp = price + 10
    else:
        sl = price + 5
        tp = price - 10

    msg = f"""XAUUSD 15M SIGNAL - Colony
Action: {action}
Entry: {price}
STOP LOSS: {sl}
TAKE PROFIT: {tp}
Risk:Reward = 1:2
Timeframe: 15M Only"""

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
