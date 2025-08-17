# main.py
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
import configparser
# 导入两个检查函数
from scanner import run_market_scan, check_stock_signal, check_crypto_signal
from telegram_bot import send_telegram_message

def job():
    """定义需要定时执行的核心任务"""
    print(f"\n🚀 Starting new scan job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # 扫描不同市场的股票
    us_signals = run_market_scan(config['MARKETS']['us_stocks_path'], check_stock_signal)
    hk_signals = run_market_scan(config['MARKETS']['hk_stocks_path'], check_stock_signal)
    
    # --- 新增：扫描加密货币市场 ---
    crypto_signals = run_market_scan(config['MARKETS']['crypto_symbols_path'], check_crypto_signal)
    
    # 格式化消息并发送
    today_str = datetime.now().strftime('%Y-%m-%d')
    message = f"*📈 Universal MTF 策略信号 - {today_str}*\n\n"
    
    has_signal = False
    if us_signals:
        message += "*🇺🇸 美股买入信号:*\n`" + "`, `".join(us_signals) + "`\n\n"
        has_signal = True
    
    if hk_signals:
        message += "*🇭🇰 港股买入信号:*\n`" + "`, `".join(hk_signals) + "`\n\n"
        has_signal = True
        
    if crypto_signals:
        message += "*₿ 加密货币买入信号:*\n`" + "`, `".join(crypto_signals) + "`\n\n"
        has_signal = True
        
    if not has_signal:
        message += "今日无任何市场触发买入信号。"
        
    send_telegram_message(message)
    print(f"✅ Scan job finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ... (main 函数和 if __name__ == "__main__": 部分保持不变) ...
def main():
    load_dotenv()
    
    print("--- 🤖 Trading Signal Scanner Initialized ---")
    print("Scheduler is running. Waiting for the scheduled time to run the job.")
    print("Press Ctrl+C to exit.")

    # 调度任务
    schedule.every().day.at("17:00").do(job)

    # 方便测试：立即运行一次
    job() 

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
