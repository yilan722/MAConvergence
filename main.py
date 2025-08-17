# main.py
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
import configparser
from scanner import run_market_scan
from telegram_bot import send_telegram_message

def job():
    """定义需要定时执行的核心任务"""
    print(f"\n🚀 Starting new scan job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # 扫描不同市场的股票
    # 注意：A股的数据获取方式(Tushare)与美股/港股(yfinance)不同，需要在scanner.py中适配
    # 这里为了简化，我们暂时只扫描美股和港股
    us_signals = run_market_scan(config['MARKETS']['us_stocks_path'])
    hk_signals = run_market_scan(config['MARKETS']['hk_stocks_path'])
    
    # 格式化消息并发送
    today_str = datetime.now().strftime('%Y-%m-%d')
    message = f"*📈 Universal MTF 策略信号 - {today_str}*\n\n"
    
    if us_signals:
        message += "*🇺🇸 美股买入信号:*\n" + "\n".join(us_signals) + "\n\n"
    
    if hk_signals:
        message += "*🇭🇰 港股买入信号:*\n" + "\n".join(hk_signals) + "\n\n"
        
    if not us_signals and not hk_signals:
        message += "今日无任何市场触发买入信号。"
        
    send_telegram_message(message)
    print(f"✅ Scan job finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    load_dotenv()
    
    print("--- 🤖 Trading Signal Scanner Initialized ---")
    print("Scheduler is running. Waiting for the scheduled time to run the job.")
    print("Press Ctrl+C to exit.")

    # 设置调度任务：每天下午5点（美股收盘后）运行一次
    # 请根据您的时区和目标市场调整时间
    schedule.every().day.at("17:00").do(job)

    # 方便测试：立即运行一次
    job() 

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
