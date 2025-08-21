# main.py (V4.4 - Final & Complete with Warning Suppression)
import warnings
# 忽略所有 FutureWarning，让日志更干净
warnings.simplefilter(action='ignore', category=FutureWarning)

import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import configparser
import os
from pathlib import Path

# --- 健壮的 .env 加载与验证 ---
script_dir = Path(__file__).resolve().parent
print(f"👋 Script directory is: {script_dir}")

dotenv_path = script_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

tushare_token_loaded = os.getenv('TUSHARE_TOKEN')
if tushare_token_loaded:
    print("✅ Tushare token loaded successfully from .env file.")
else:
    print("⚠️  Warning: Tushare token NOT found in environment variables.")
# --- 加载完成 ---

from scanner import scan_markets_for_last_signal
from telegram_bot import send_telegram_message

def job():
    print(f"\n🚀 Starting new scan job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    recency_days = int(config['REPORTING']['RECENCY_DAYS'])
    
    us_signals = scan_markets_for_last_signal(config['MARKETS']['us_stocks_path'], 'stock')
    hk_signals = scan_markets_for_last_signal(config['MARKETS']['hk_stocks_path'], 'stock')
    cn_signals = scan_markets_for_last_signal(config['MARKETS']['cn_stocks_path'], 'cn_stock')
    crypto_signals = scan_markets_for_last_signal(config['MARKETS']['crypto_symbols_path'], 'crypto')
    
    today = datetime.now()
    cutoff_date = today - timedelta(days=recency_days)
    
    message = f"*📈 最近{recency_days}天内的买入信号*\n_{today.strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
    
    def filter_and_sort_signals(signals_dict):
        recent_signals = {
            ticker: date_str for ticker, date_str in signals_dict.items()
            if datetime.strptime(date_str, '%Y-%m-%d') >= cutoff_date
        }
        return sorted(recent_signals.items(), key=lambda item: item[1], reverse=True)

    us_sorted = filter_and_sort_signals(us_signals)
    hk_sorted = filter_and_sort_signals(hk_signals)
    cn_sorted = filter_and_sort_signals(cn_signals)
    crypto_sorted = filter_and_sort_signals(crypto_signals)
    
    has_signal = False
    if us_sorted:
        message += "*🇺🇸 美股信号:*\n"
        for ticker, date in us_sorted:
            message += f"`{ticker:<8}` | {date}\n"
        message += "\n"
        has_signal = True
    
    if hk_sorted:
        message += "*🇭🇰 港股信号:*\n"
        for ticker, date in hk_sorted:
            message += f"`{ticker:<8}` | {date}\n"
        message += "\n"
        has_signal = True
        
    if cn_sorted:
        message += "*🇨🇳 A股信号:*\n"
        for ticker, date in cn_sorted:
            message += f"`{ticker:<10}` | {date}\n"
        message += "\n"
        has_signal = True
        
    if crypto_sorted:
        message += "*₿ 加密货币信号:*\n"
        for ticker, date in crypto_sorted:
            message += f"`{ticker:<10}` | {date}\n"
        message += "\n"
        has_signal = True
        
    if not has_signal:
        message += f"最近{recency_days}天内无任何市场触发买入信号。"
        
    send_telegram_message(message)
    print(f"✅ Scan job finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    print("--- 🤖 Advanced Signal Scanner (All Markets) Initialized ---")
    print("Scheduler is running. Waiting for the scheduled time to run the job.")
    print("Press Ctrl+C to exit.")

    schedule.every().day.at("17:00").do(job)
    job()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
