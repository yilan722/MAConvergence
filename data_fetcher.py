# data_fetcher.py
import yfinance as yf
import tushare as ts
import pandas as pd
import os
import requests

# 初始化Tushare (如果您的.env文件中有token的话)
if os.getenv('TUSHARE_TOKEN'):
    ts.set_token(os.getenv('TUSHARE_TOKEN'))
    pro = ts.pro_api()

def get_yfinance_data(ticker, period="2y", interval="1d"):
    """使用yfinance获取美股/港股数据"""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval, auto_adjust=True)
    # yfinance列名为大写，统一为小写
    df.columns = [col.lower() for col in df.columns]
    # 确保索引名为'date'
    df.index.name = 'date'
    return df

def get_tushare_data(ticker, start_date='20220101', end_date='20251231'):
    """使用Tushare获取A股数据"""
    try:
        # Tushare的日期格式是YYYYMMDD
        df = pro.daily(ts_code=ticker, start_date=start_date, end_date=end_date)
        # Tushare返回的数据是倒序的，需要反转
        df = df.sort_values(by='trade_date', ascending=True)
        # 重命名列以匹配yfinance
        df = df.rename(columns={'trade_date': 'date', 'vol': 'volume'})
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"🔥 Error fetching {ticker} from Tushare: {e}")
        return pd.DataFrame()


def get_binance_data(symbol, interval='1d', limit=500):
    """
    使用Binance API获取加密货币K线数据。
    返回与yfinance格式兼容的DataFrame。
    """
    
    # data_fetcher.py -> get_binance_data function

# --- 根据您的网络环境，选择其中一个URL ---

# 方案A: 如果您正在使用VPN
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

# 方案B: 如果您在美国本地，没有使用VPN

    url = f"https://api.binance.us/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # 转换数据为Pandas DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # --- 关键：格式化DataFrame以匹配yfinance的输出 ---
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].astype(float)
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('date', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)
        
        return df

    except requests.RequestException as e:
        print(f"🔥 Error fetching {symbol} from Binance: {e}")
        return pd.DataFrame() # 返回空的DataFrame
