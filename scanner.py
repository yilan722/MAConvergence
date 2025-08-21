# scanner.py (V4.1 - Fixed NameError)
import pandas as pd
import pandas_ta as ta
import configparser
# --- 关键修改：在这里导入 pro ---
from data_fetcher import get_yfinance_data, get_binance_data, get_tushare_data, pro
from datetime import datetime, timedelta

# --- 辅助函数：复现Pine Script的crossover ---
def crossover(series1, series2):
    s1 = pd.Series(series1)
    s2 = pd.Series(series2)
    return (s1.shift(1) < s2.shift(1)) & (s1 > s2)

# --- 核心策略函数：寻找最后一次买入信号的日期 ---
def find_last_buy_signal_date(ticker, data_fetch_func):
    # ... (这个函数本身无需修改) ...
    try:
        if data_fetch_func.__name__ == 'get_yfinance_data':
            df = data_fetch_func(ticker, period="3y", interval="1d")
        else:
            df = data_fetch_func(ticker)

        if df.empty or len(df) < 250:
            return None
            
        # ... (后续计算逻辑完全不变) ...
        df['LT_EMA30'] = ta.ema(df['close'], length=30)
        df['LT_EMA60'] = ta.ema(df['close'], length=60)
        df['LT_EMA90'] = ta.ema(df['close'], length=90)
        df['LT_MA200'] = ta.sma(df['close'], length=200)
        df['ST_EMA21'] = ta.ema(df['close'], length=21)
        df['ST_EMA30'] = ta.ema(df['close'], length=30)
        df['ST_MA34'] = ta.sma(df['close'], length=34)
        df.dropna(inplace=True)
        if df.empty: return None

        long_term_mas = df[['LT_EMA30', 'LT_EMA60', 'LT_EMA90', 'LT_MA200']]
        df['long_cv'] = long_term_mas.std(axis=1) / long_term_mas.mean(axis=1)
        ma200_slope_val = ta.slope(df['LT_MA200'], length=10)
        df['slope_ma200'] = ma200_slope_val / df['LT_MA200']
        
        condition1 = (df['long_cv'] < 0.02) & (df['slope_ma200'] > -0.001)
        
        was_ma200_support = df['low'].rolling(window=20).min() < df['LT_MA200'].rolling(window=20).min() * 1.01
        is_above_ma200 = df['close'] > df['LT_MA200']
        condition2 = was_ma200_support & is_above_ma200

        short_term_mas = df[['ST_EMA21', 'ST_EMA30', 'ST_MA34']]
        df['short_cv'] = short_term_mas.std(axis=1) / short_term_mas.mean(axis=1)
        condition3 = df['short_cv'].shift(1) < 0.005

        df['short_resistance'] = short_term_mas.max(axis=1)
        condition4 = crossover(df['close'], df['short_resistance'])

        df['buy_signal'] = condition1 & condition2 & condition3 & condition4

        signal_dates = df.index[df['buy_signal']]
        
        if not signal_dates.empty:
            last_signal_date = signal_dates[-1]
            return last_signal_date.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"❌ Error processing {ticker} for last signal date: {e}")
        
    return None

# --- 升级后的扫描主函数 (无需修改) ---
def scan_markets_for_last_signal(stock_list_path, market_type):
    signal_results = {}
    
    if market_type == 'crypto':
        data_fetch_func = get_binance_data
    elif market_type == 'cn_stock':
        data_fetch_func = get_tushare_data
    else:
        data_fetch_func = get_yfinance_data

    with open(stock_list_path, 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    
    # 这里的 pro 已经从文件顶部导入，所以不再报错
    if market_type == 'cn_stock' and (not tickers or not pro):
        if not pro: print("ℹ️  Skipping A-share scan because Tushare token is not set.")
        return {}

    print(f"\n--- Scanning {len(tickers)} symbols from {stock_list_path} for last signal date ---")
    for ticker in tickers:
        last_date = find_last_buy_signal_date(ticker, data_fetch_func)
        if last_date:
            signal_results[ticker] = last_date
            
    return signal_results
