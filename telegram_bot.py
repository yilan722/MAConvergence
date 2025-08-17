# telegram_bot.py
import telegram
import os

def send_telegram_message(message_text):
    """向指定的Telegram聊天发送消息"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("🔴 Telegram TOKEN or CHAT_ID not set in .env file.")
        return

    try:
        bot = telegram.Bot(token=token)
        bot.send_message(chat_id=chat_id, text=message_text, parse_mode=telegram.ParseMode.MARKDOWN)
        print("📬 Telegram message sent successfully!")
    except Exception as e:
        print(f"🔥 Error sending Telegram message: {e}")
