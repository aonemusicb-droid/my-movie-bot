import nest_asyncio
import asyncio
import requests
import os
import threading
from flask import Flask
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

nest_asyncio.apply()

# --- Render-ന് വേണ്ടി Flask ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot is Alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8427226244:AAHvNhWJb6QZOH2gOa5wFqBaeu2ilp0H3_I"

app = Client("InstantMailBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User session storage
user_mails = {}

def get_clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")

async def check_messages(client, chat_id, user, domain):
    seen_ids = set()
    print(f"Checking mail for {user}@{domain}...")
    
    while user_mails.get(chat_id) == f"{user}@{domain}":
        try:
            url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={user}&domain={domain}"
            resp = requests.get(url).json()
            
            for msg in resp:
                if msg['id'] not in seen_ids:
                    seen_ids.add(msg['id'])
                    # Fetch full content
                    msg_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={user}&domain={domain}&id={msg['id']}"
                    full_msg = requests.get(msg_url).json()
                    
                    output = (
                        f"📬 **New Mail Received!**\n\n"
                        f"👤 **From:** `{full_msg['from']}`\n"
                        f"📝 **Subject:** {full_msg['subject']}\n"
                        f"📅 **Date:** {full_msg['date']}\n\n"
                        f"📄 **Message:**\n{get_clean_text(full_msg['body'])[:3800]}"
                    )
                    await client.send_message(chat_id, output)
        except:
            pass
        await asyncio.sleep(6)

@app.on_message(filters.command("start"))
async def start(client, message):
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("Generate Random Mail 🎲", callback_data="gen")]])
    await message.reply("Welcome! Click below to get a temporary email address.", reply_markup=btn)

@app.on_callback_query(filters.regex("gen"))
async def generate(client, query):
    res = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1").json()
    email = res[0]
    user, domain = email.split("@")
    user_mails[query.from_user.id] = email
    
    await query.message.edit_text(
        f"📧 **Your Temp Email:**\n`{email}`\n\n"
        "I am monitoring your inbox. You will receive a message here when an email arrives!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Refresh / New 🔄", callback_data="gen")]])
    )
    asyncio.create_task(check_messages(client, query.from_user.id, user, domain))

# Start the bot
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Starting Bot...")
    app.run()
