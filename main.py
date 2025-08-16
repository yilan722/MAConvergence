# main.py
import yfinance as yf
import pandas as pd
from ta.trend import ema_indicator
import requests
import os
from datetime import datetime

# === 配置 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STOCKS = {
    'A股': ['600519.SS', '000858.SZ'],
    '港股': ['0700.HK', '9988.HK'],
    '美股': ['NVDA', 'AAPL']
}

def check_signal(symbol):
    try:
        data = yf.download(symbol, period="6mo", interval="1d")
        if len(data) < 90: return None
        data['EMA30'] = ema_indicator(data['Close'], 30)
        data['EMA90'] = ema_indicator(data['Close'], 90)
        curr = data.iloc[-1]
        prev = data.iloc[-2]
        if prev['EMA30'] <= prev['EMA90'] and curr['EMA30'] > curr['EMA90']:
            return {'symbol': symbol, 'price': round(curr['Close'], 2)}
    except: return None

signals = []
for market, syms in STOCKS.items():
    for s in syms:
        if res := check_signal(s):
            signals.append(f"✅ {market} {res['symbol']} {res['price']}")

msg = f"🎯 买入信号 ({datetime.now().strftime('%Y-%m-%d')})\n" + \
      ("\n".join(signals) if signals else "🟢 无信号")

# 发送到 Telegram
requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
)
