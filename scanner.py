# scanner.py
import pandas as pd
import pandas_ta as ta
import configparser
# 我们现在从这里导入所有数据获取函数
from data_fetcher import get_yfinance_data, get_binance_data

# --- 辅助函数：复现Pine Script的crossover (不变) ---
def crossover(series1, series2):
    return (series1.shift(1) < series2.shift(1)) & (series1 > series2)

# --- 这是重构后的通用信号检查函数 ---
def check_signal_generic(ticker, main_fetch_func, trend_fetch_func):
    """
    通用的信号检查逻辑，可以处理任何来源的数据。
    """
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        params = config['STRATEGY']
        
        bb_length = int(params['bb_length'])
        bb_mult = float(params['bb_mult'])
        ema_fast_length = int(params['ema_fast_length'])
        ema_slow_length = int(params['ema_slow_length'])

        # 2. 使用传入的函数获取数据
        main_df = main_fetch_func(ticker)
        if main_df.empty or len(main_df) < bb_length:
            return False

        trend_df = trend_fetch_func(ticker)
        if trend_df.empty:
            return False

        # 3. 计算指标 (逻辑完全不变)
        trend_df['ema_fast'] = ta.ema(trend_df['close'], length=ema_fast_length)
        trend_df['ema_slow'] = ta.ema(trend_df['close'], length=ema_slow_length)
        
        # 将趋势数据合并到主周期
        main_df = main_df.join(trend_df[['ema_fast', 'ema_slow']].rename(columns={
            'ema_fast': 'trend_ema_fast',
            'ema_slow': 'trend_ema_slow'
        }))
        main_df['trend_ema_fast'].ffill(inplace=True)
        main_df['trend_ema_slow'].ffill(inplace=True)
        
        main_df.ta.bbands(length=bb_length, std=bb_mult, append=True, col_names=(f'BBL_{bb_length}_{bb_mult}', f'BBM_{bb_length}_{bb_mult}', f'BBU_{bb_length}_{bb_mult}', f'BBB_{bb_length}_{bb_mult}', f'BBP_{bb_length}_{bb_mult}'))
        main_df['ema_fast'] = ta.ema(main_df['close'], length=ema_fast_length)
        main_df['ema_slow'] = ta.ema(main_df['close'], length=ema_slow_length)
        main_df.dropna(inplace=True)

        # 4. 复现策略条件 (逻辑完全不变)
        if main_df.empty: return False
        latest_data = main_df.iloc[-1]

        can_look_for_buy = latest_data['trend_ema_fast'] > latest_data['trend_ema_slow']
        buySignal_BB_Break = crossover(main_df['close'], main_df[f'BBM_{bb_length}_{bb_mult}']).iloc[-1]
        main_tf_bullish_cross = crossover(main_df['ema_fast'], main_df['ema_slow']).iloc[-1]
        
        if can_look_for_buy and (buySignal_BB_Break or (latest_data['close'] > latest_data[f'BBM_{bb_length}_{bb_mult}'] and main_tf_bullish_cross)):
            print(f"✅ BUY SIGNAL DETECTED for {ticker}")
            return True

    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
    
    return False

# --- 创建针对不同资产类别的 "包装器" 函数 ---
def check_stock_signal(ticker):
    """检查股票信号 (使用yfinance)"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    trend_tf_stock = config['STRATEGY']['trend_timeframe'] # '60m'
    
    # yfinance的时间周期字符串需要调整
    if 'm' not in trend_tf_stock: trend_tf_stock = '60m'
    
    return check_signal_generic(
        ticker,
        main_fetch_func=lambda t: get_yfinance_data(t, period="2y", interval="1d"),
        trend_fetch_func=lambda t: get_yfinance_data(t, period="730d", interval=trend_tf_stock)
    )

def check_crypto_signal(ticker):
    """检查加密货币信号 (使用Binance)"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    trend_tf_crypto = config['CRYPTO_SETTINGS']['trend_timeframe_crypto'] # '1h'

    return check_signal_generic(
        ticker,
        main_fetch_func=lambda t: get_binance_data(t, interval="1d", limit=500),
        trend_fetch_func=lambda t: get_binance_data(t, interval=trend_tf_crypto, limit=1000)
    )

# --- run_market_scan现在接受一个检查函数作为参数 ---
def run_market_scan(stock_list_path, check_function):
    """遍历股票列表，使用指定的检查函数返回触发信号的股票"""
    triggered_stocks = []
    with open(stock_list_path, 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    
    print(f"\n--- Scanning {len(tickers)} symbols from {stock_list_path} ---")
    for ticker in tickers:
        if check_function(ticker):
            triggered_stocks.append(ticker)
    
    return triggered_stocks
