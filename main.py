import os, threading, time
import yfinance as yf
import pandas as pd
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- TRADING LOGIC ---
def get_signal():
    try:
        # Download XAUUSD 15m candles
        df = yf.download("GC=F", period="2d", interval="15m", progress=False)
        if df.empty:
            return None
        # Flatten columns if needed
        if hasattr(df.columns, 'get_level_values'):
            try: df.columns = df.columns.get_level_values(0)
            except: pass
        df['EMA9'] = df['Close'].ewm(span=9).mean()
        df['EMA21'] = df['Close'].ewm(span=21).mean()
        # RSI 14
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(last['Close'])
        ema9 = float(last['EMA9'])
        ema21 = float(last['EMA21'])
        rsi = float(last['RSI'])
        
        # BUY: EMA9 cross above EMA21 + RSI < 70 and > 50
        if prev['EMA9'] < prev['EMA21'] and ema9 > ema21 and 50 < rsi < 70:
            return f"🟢 BUY XAUUSD\nEntry: {price:.2f}\nSL: {price-5:.2f}\nTP: {price+10:.2f}\nEMA9: {ema9:.2f} > EMA21: {ema21:.2f}\nRSI: {rsi:.1f}"
        # SELL: EMA9 cross below EMA21 + RSI > 30 and < 50
        if prev['EMA9'] > prev['EMA21'] and ema9 < ema21 and 30 < rsi < 50:
            return f"🔴 SELL XAUUSD\nEntry: {price:.2f}\nSL: {price+5:.2f}\nTP: {price-10:.2f}\nEMA9: {ema9:.2f} < EMA21: {ema21:.2f}\nRSI: {rsi:.1f}"
        return f"⏳ No signal now\nPrice: {price:.2f} | EMA9: {ema9:.2f} | EMA21: {ema21:.2f} | RSI: {rsi:.1f}"
    except Exception as e:
        return f"Error checking: {e}"

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Colony XAUUSD Bot ONLINE!\nStrategy: EMA9 + EMA21 + RSI14 (15m)\nSend /signal to check now. I go send signal automatically every 15m.")

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Checking XAUUSD 15m...")
    msg = get_signal()
    await update.message.reply_text(msg)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /signal to check XAUUSD now.")

def run_bot():
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("signal", signal_cmd))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # Auto-check every 15m in background
    def auto_loop():
        import asyncio
        while True:
            time.sleep(900) # 15 mins
            try:
                msg = get_signal()
                if msg and ("BUY" in msg or "SELL" in msg):
                    # send via bot
                    import requests
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🚨 AUTO SIGNAL\n" + msg})
            except Exception as e:
                print(e)
    threading.Thread(target=auto_loop, daemon=True).start()
    bot_app.run_polling()

@app.route("/")
def home():
    return "XAUUSD Bot Live!"

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
