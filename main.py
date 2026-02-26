import nest_asyncio
import asyncio
import requests
import qrcode
import io
import os
import threading
from flask import Flask
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

nest_asyncio.apply()

# --- FLASK SERVER ---
flask_app = Flask(__name__)
@flask_app.route('/')
def health_check():
    return "SwiftFakeMailBot is active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False)

# --- CONFIGURATION ---
API_KEY = "7jkmE5NM2VS6GqJ9pzlI"
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8427226244:AAG9sDCHxaQm3IcRjzQimz0MTcEmOr_dvd0"

app = Client("SwiftFakeMailBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

# --- UTILS ---
def clean_html(raw_html):
    if not raw_html: return "No content"
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n")

async def monitor_inbox(client, chat_id, email):
    """Improved Monitor for Priyo API"""
    seen_ids = set()
    print(f"DEBUG: Monitoring started for {email}")
    
    # Initial load to avoid old spam
    try:
        url = f"https://free.priyo.email/api/messages/{email}/{API_KEY}"
        res = requests.get(url).json()
        if isinstance(res, list):
            for m in res:
                seen_ids.add(m.get('id'))
    except Exception as e:
        print(f"DEBUG: Initial fetch error: {e}")

    while user_data.get(chat_id, {}).get("email") == email:
        try:
            url = f"https://free.priyo.email/api/messages/{email}/{API_KEY}"
            response = requests.get(url)
            
            # API ചിലപ്പോൾ error message അയക്കാം, അത് ഒഴിവാക്കാൻ:
            if response.status_code != 200:
                await asyncio.sleep(10)
                continue
                
            msgs = response.json()
            
            if isinstance(msgs, list):
                for m in msgs:
                    msg_id = m.get('id')
                    if msg_id and msg_id not in seen_ids:
                        seen_ids.add(msg_id)
                        
                        sender = m.get('sender', 'Unknown')
                        subject = m.get('subject', 'No Subject')
                        body = clean_html(m.get('message', 'No content'))
                        
                        text = (
                            f"📩 **New Email Received!**\n\n"
                            f"📧 **To:** `{email}`\n"
                            f"👤 **From:** {sender}\n"
                            f"📝 **Subject:** {subject}\n\n"
                            f"📄 **Content:**\n{body[:3500]}"
                        )
                        
                        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Delete", callback_data=f"del_{msg_id}")]])
                        await client.send_message(chat_id, text, reply_markup=btn)
            
            # API rate limit ഒഴിവാക്കാൻ 10 സെക്കന്റ് ഗ്യാപ്പ് നൽകുന്നു
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"DEBUG: Loop Error: {e}")
            await asyncio.sleep(10)

# --- COMMANDS ---
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    welcome = (
        "⚡️ **Swift Fake Mail Bot**\n\n"
        "Your private mailbox is ready. Send any text to set a custom username or click below for a random one."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Random Email", callback_data="gen_rand")],
        [InlineKeyboardButton("🌐 Domains", callback_data="list_dom")],
        [InlineKeyboardButton("🖼 QR Code", callback_data="qr_gen")]
    ])
    await message.reply(welcome, reply_markup=buttons)

@app.on_message(filters.text & filters.private)
async def handle_custom_name(client, message):
    uid = message.from_user.id
    if message.text.startswith("/"): return
    
    # Custom name set ചെയ്യുമ്പോൾ ഡൊമൈൻ കൂടി വേണം
    try:
        dom_url = f"https://free.priyo.email/api/domains/{API_KEY}"
        domains = requests.get(dom_url).json()
        domain = domains[0] if domains else "priyo.email"
        
        name = "".join(e for e in message.text if e.isalnum()).lower()
        email = f"{name}@{domain}"
        
        user_data[uid] = {"email": email}
        await message.reply(f"✅ **Email Set:** `{email}`\nWaiting for messages... 📬")
        asyncio.create_task(monitor_inbox(client, uid, email))
    except:
        await message.reply("❌ Error setting email. Try random.")

@app.on_callback_query()
async def cb_handler(client, query):
    uid = query.from_user.id
    data = query.data

    if data == "gen_rand":
        try:
            url = f"https://free.priyo.email/api/random-email/{API_KEY}"
            res = requests.get(url).json()
            email = res['email']
            user_data[uid] = {"email": email}
            
            await query.message.edit_text(f"✅ **Generated:** `{email}`\n\nWaiting for messages... 📬")
            asyncio.create_task(monitor_inbox(client, uid, email))
        except:
            await query.answer("API Error. Try again.", show_alert=True)

    elif data == "list_dom":
        try:
            url = f"https://free.priyo.email/api/domains/{API_KEY}"
            domains = requests.get(url).json()
            await query.message.edit_text(f"Available Domains:\n\n" + "\n".join(domains))
        except: await query.answer("Error")

    elif data.startswith("del_"):
        msg_id = data.split("_")[1]
        try:
            url = f"https://free.priyo.email/api/message/{msg_id}/{API_KEY}"
            requests.delete(url)
            await query.answer("Deleted!")
            await query.message.delete()
        except: pass

# --- MAIN ---
async def start_bot():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    print("Bot Started!")
    await asyncio.Future()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
