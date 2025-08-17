# scanner.py
import pandas as pd
import pandas_ta as ta
import configparser
from data_fetcher import get_yfinance_data

# --- 辅助函数：复现Pine Script的crossover ---
def crossover(series1, series2):
    return (series1.shift(1) < series2.shift(1)) & (series1 > series2)

def check_buy_signal(ticker, trend_timeframe='60m'):
    """
    核心函数：获取数据并检查买入信号
    """
    try:
        # 1. 读取策略参数
        config = configparser.ConfigParser()
        config.read('config.ini')
        params = config['STRATEGY']
        
        bb_length = int(params['bb_length'])
        bb_mult = float(params['bb_mult'])
        ema_fast_length = int(params['ema_fast_length'])
        ema_slow_length = int(params['ema_slow_length'])

        # 2. 获取多时间周期（MTF）数据
        # 获取主周期（日线）数据
        main_df = get_yfinance_data(ticker, period="2y", interval="1d")
        if main_df.empty or len(main_df) < bb_length:
            return False

        # 获取趋势过滤周期（例如60分钟）数据
        trend_df = get_yfinance_data(ticker, period="730d", interval=trend_timeframe) # 730d获取更多数据
        if trend_df.empty:
            return False

        # 3. 计算指标
        # 计算趋势周期的EMA
        trend_df['ema_fast'] = ta.ema(trend_df['close'], length=ema_fast_length)
        trend_df['ema_slow'] = ta.ema(trend_df['close'], length=ema_slow_length)
        
        # 将趋势周期的EMA信号合并到主周期的DataFrame中
        # resample('D').last() 将小时线数据转换为日线数据，取每天最后一个值
        main_df['trend_ema_fast'] = trend_df['ema_fast'].reindex(main_df.index, method='ffill')
        main_df['trend_ema_slow'] = trend_df['ema_slow'].reindex(main_df.index, method='ffill')
        
        # 计算主周期的指标
        main_df.ta.bbands(length=bb_length, std=bb_mult, append=True) # 会自动添加 BB_basis, BB_upper, BB_lower列
        main_df['ema_fast'] = ta.ema(main_df['close'], length=ema_fast_length)
        main_df['ema_slow'] = ta.ema(main_df['close'], length=ema_slow_length)
        main_df.dropna(inplace=True)

        # 4. 复现策略条件
        latest_data = main_df.iloc[-1] # 获取最新一天（昨日）的数据

        # 趋势条件：趋势周期的快线 > 慢线
        can_look_for_buy = latest_data['trend_ema_fast'] > latest_data['trend_ema_slow']
        
        # 信号条件1：价格上穿BB中轨
        buySignal_BB_Break = crossover(main_df['close'], main_df[f'BBM_{bb_length}_{bb_mult}']).iloc[-1]

        # 信号条件2：主周期EMA金叉
        main_tf_bullish_cross = crossover(main_df['ema_fast'], main_df['ema_slow']).iloc[-1]
        
        # 综合判断
        if can_look_for_buy and (buySignal_BB_Break or (latest_data['close'] > latest_data[f'BBM_{bb_length}_{bb_mult}'] and main_tf_bullish_cross)):
            print(f"✅ BUY SIGNAL DETECTED for {ticker}")
            return True

    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
    
    return False

def run_market_scan(stock_list_path):
    """遍历股票列表，返回触发信号的股票"""
    triggered_stocks = []
    with open(stock_list_path, 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    
    print(f"\n--- Scanning {len(tickers)} stocks from {stock_list_path} ---")
    for ticker in tickers:
        if check_buy_signal(ticker):
            triggered_stocks.append(ticker)
    
    return triggered_stocks
