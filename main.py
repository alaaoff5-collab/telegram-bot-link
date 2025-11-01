import threading
import http.server
import socketserver
import os
import sqlite3
import asyncio
from telethon import TelegramClient
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, MessageHandler, CallbackContext, filters

# --------------------------
# إبقاء التطبيق حيًّا على Koyeb
def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"🌐 Web server running on port {port} to keep Koyeb alive...")
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()
# --------------------------

# بيانات البوت الأول
bot_token = '8440318160:AAF5HYHb0iwIe6HFHMk3ykqabrOpJdA7K28'

# بيانات حسابك الشخصي
api_id = 26299944
api_hash = '9adcc1a849ef755bef568475adebee77'
bot2_username = '@tg_acccobot'

# قاعدة البيانات
conn = sqlite3.connect('user_balances.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS balances
                  (chat_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)''')
conn.commit()

def get_balance(chat_id):
    cursor.execute("SELECT balance FROM balances WHERE chat_id=?", (chat_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_balance(chat_id, amount):
    cursor.execute("INSERT OR IGNORE INTO balances (chat_id, balance) VALUES (?,0)", (chat_id,))
    cursor.execute("UPDATE balances SET balance = balance + ? WHERE chat_id=?", (amount, chat_id))
    conn.commit()

client = TelegramClient('session', api_id, api_hash)

updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    lower_text = text.lower() if text else ""

    if "balance" in lower_text or "رصيد" in lower_text:
        balance = get_balance(chat_id)
        context.bot.send_message(chat_id=chat_id, text=f"Your current balance is: {balance}")
        return

    if "withdraw" in lower_text or "سحب" in lower_text:
        context.bot.send_message(chat_id=chat_id, text="Your withdrawal request has been sent to admins for approval")
        return

    async def send_to_bot2():
        await client.send_message(bot2_username, text)
        response = await client.get_messages(bot2_username, limit=1)
        if response:
            reply_msg = response[0]
            reply = reply_msg.text or ""

            if "Please enter the amount you want to withdraw" in reply:
                reply = "Please enter the amount you want to withdraw (Minimum: 100.0)"

            if "+" in reply:
                try:
                    amount = float(reply.split("+")[1].split()[0])
                    update_balance(chat_id, amount)
                except:
                    pass

            buttons = []
            if reply_msg.reply_markup and reply_msg.reply_markup.rows:
                for row in reply_msg.reply_markup.rows:
                    buttons.append([InlineKeyboardButton(btn.text, callback_data=btn.text) for btn in row.buttons])

            markup = InlineKeyboardMarkup(buttons) if buttons else None
            context.bot.send_message(chat_id=chat_id, text=reply, reply_markup=markup)

    asyncio.run(send_to_bot2())

dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def main():
    await client.start()
    print("✅ Personal Telegram Client running...")
    updater.start_polling()
    updater.idle()

asyncio.run(main())
