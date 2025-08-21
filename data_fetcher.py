# data_fetcher.py (V3.1 - Tushare Retry Logic)
import yfinance as yf
import tushare as ts
import pandas as pd
import os
import requests
import time
from datetime import datetime, timedelta

# --- Tushare 初始化 ---
tushare_token = os.getenv('TUSHARE_TOKEN')
if tushare_token:
    ts.set_token(tushare_token)
    pro = ts.pro_api()
else:
    pro = None

def get_yfinance_data(ticker, period="3y", interval="1d", retries=3, delay=5):
    """
    [升级版] 使用yfinance获取美股/港股数据，并增加了自动重试和更友好的错误处理。
    """
    for i in range(retries):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval, auto_adjust=True)
            if not df.empty:
                df.columns = [col.lower() for col in df.columns]
                df.index.name = 'date'
                return df
            else:
                print(f"ℹ️  No data found for {ticker} on Yahoo Finance. It may be delisted or the ticker is incorrect.")
                return pd.DataFrame()
        except Exception as e:
            print(f"⚠️  Attempt {i+1}/{retries} failed for {ticker}: {e}")
            if i < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"❌ All retries failed for {ticker}.")
    return pd.DataFrame()

def get_binance_data(symbol, interval='1d', limit=1000):
    """
    使用Binance API获取加密货币K线数据。
    返回与yfinance格式兼容的DataFrame。
    """
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].astype(float)
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('date', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)
        return df
    except requests.RequestException as e:
        if '400' in str(e): print(f"⚠️  Warning: Symbol {symbol} may not exist on Binance. Skipping.")
        else: print(f"🔥 Error fetching {symbol} from Binance: {e}")
        return pd.DataFrame()

def get_tushare_data(ticker, period="3y", interval="1d", retries=3, delay=10):
    """
    [升级版] 使用Tushare获取A股日线数据，并增加重试逻辑。
    """
    if not pro:
        print("🔴 Tushare token not configured. Skipping A-share market.")
        return pd.DataFrame()

    for i in range(retries):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3 * 365)
            end_date_str = end_date.strftime('%Y%m%d')
            start_date_str = start_date.strftime('%Y%m%d')
            
            df = ts.pro_bar(ts_code=ticker, adj='qfq', start_date=start_date_str, end_date=end_date_str)
            
            if df is not None and not df.empty:
                df = df.sort_values(by='trade_date', ascending=True)
                df = df.rename(columns={'trade_date': 'date', 'vol': 'volume'})
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']]
                return df
        except Exception as e:
            print(f"⚠️  Attempt {i+1}/{retries} failed for {ticker} from Tushare: {e}")
            if i < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay) # Tushare接口限制更严，等待时间更长
            else:
                print(f"❌ All retries failed for {ticker} from Tushare.")
    return pd.DataFrame()
