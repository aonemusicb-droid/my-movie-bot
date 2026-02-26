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
    flask_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_KEY = "7jkmE5NM2VS6GqJ9pzlI"
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8427226244:AAFDm0Kip4VnROOzCDO0GWE5cx4nmCGKRQE"

app = Client("SwiftFakeMailBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

# --- UTILS ---
def clean_html(raw_html):
    if not raw_html: return "No content"
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n")

async def monitor_inbox(client, chat_id, email):
    """Monitor inbox using the new Priyo API"""
    seen_ids = set()
    
    # Initial check to skip old messages
    try:
        url = f"https://free.priyo.email/api/messages/{email}/{API_KEY}"
        res = requests.get(url).json()
        if isinstance(res, list):
            seen_ids = {m['id'] for m in res}
    except: pass

    while user_data.get(chat_id, {}).get("email") == email:
        try:
            url = f"https://free.priyo.email/api/messages/{email}/{API_KEY}"
            msgs = requests.get(url).json()
            
            if isinstance(msgs, list):
                for m in msgs:
                    if m['id'] not in seen_ids:
                        seen_ids.add(m['id'])
                        
                        text = (
                            f"📩 **New Email Received!**\n\n"
                            f"📧 **To:** `{email}`\n"
                            f"👤 **From:** {m['sender']}\n"
                            f"📝 **Subject:** {m['subject']}\n\n"
                            f"📄 **Content:**\n{clean_html(m['message'])}"
                        )
                        # Delete button option
                        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Delete Message", callback_data=f"del_{m['id']}")]])
                        await client.send_message(chat_id, text, reply_markup=btn)
        except Exception as e:
            print(f"Monitoring Error: {e}")
            
        await asyncio.sleep(6)

# --- COMMANDS ---
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    welcome = (
        "⚡️ **Swift Fake Mail Bot**\n\n"
        "Your temporary mailbox service is ready. Use the buttons below to manage your emails.\n\n"
        "• **Status:** Connected ✅\n"
        "• **API:** Priyo Premium"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Random Email", callback_data="gen_rand")],
        [InlineKeyboardButton("🌐 Available Domains", callback_data="list_dom")],
        [InlineKeyboardButton("🖼 Get QR Code", callback_data="qr_gen")]
    ])
    await message.reply(welcome, reply_markup=buttons)

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
            await query.answer("Failed to generate. Try again.", show_alert=True)

    elif data == "list_dom":
        try:
            url = f"https://free.priyo.email/api/domains/{API_KEY}"
            domains = requests.get(url).json()
            text = "🏠 **Available Domains:**\n\n" + "\n".join([f"• `{d}`" for d in domains])
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
        except:
            await query.answer("Could not fetch domains.")

    elif data.startswith("del_"):
        msg_id = data.split("_")[1]
        url = f"https://free.priyo.email/api/message/{msg_id}/{API_KEY}"
        requests.delete(url)
        await query.message.edit_text("🗑 Message deleted successfully.")

    elif data == "qr_gen":
        email = user_data.get(uid, {}).get("email")
        if not email: return await query.answer("Generate an email first!", show_alert=True)
        img = qrcode.make(email); buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
        await query.message.reply_photo(buf, caption=f"Scan to copy: {email}")

    elif data == "back":
        await start_cmd(client, query.message)

# --- MAIN ---
async def start_bot():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    print("Bot is ONLINE with Priyo API!")
    await asyncio.Future()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
