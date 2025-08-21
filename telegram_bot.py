# telegram_bot.py (V2.1 - with Retry Logic)
import asyncio
import os
import time
from telegram import Bot
from telegram.constants import ParseMode

async def send_telegram_message_async(message_text):
    """
    [新版本] 异步函数，用于向指定的Telegram聊天发送消息。
    """
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("🔴 Telegram TOKEN or CHAT_ID not set in .env file.")
        return
        
    bot = Bot(token=token)
    await bot.send_message(
        chat_id=chat_id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN
    )

def send_telegram_message(message_text, retries=3, delay=5):
    """
    [升级版] 同步包装器，增加了自动重试功能。
    """
    for i in range(retries):
        try:
            print(f"Attempting to send Telegram message (Attempt {i+1}/{retries})...")
            asyncio.run(send_telegram_message_async(message_text))
            print("📬 Telegram message sent successfully!")
            return # 成功后直接返回
        except Exception as e:
            print(f"🔥 Error sending Telegram message: {e}")
            if i < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("❌ All retries failed for sending Telegram message.")
