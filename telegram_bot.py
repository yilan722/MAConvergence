# telegram_bot.py
import asyncio
import os
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

    try:
        bot = Bot(token=token)
        await bot.send_message(
            chat_id=chat_id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN
        )
        print("📬 Telegram message sent successfully!")
    except Exception as e:
        print(f"🔥 Error sending Telegram message: {e}")

def send_telegram_message(message_text):
    """
    [同步包装器] 方便在我们的主程序(main.py)中以同步方式调用。
    """
    try:
        # 使用asyncio.run来执行异步函数
        asyncio.run(send_telegram_message_async(message_text))
    except Exception as e:
        print(f"🔥 Error in asyncio wrapper for Telegram: {e}")
