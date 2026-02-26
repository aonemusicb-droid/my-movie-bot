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

# Apply nest_asyncio for Render/Python environment compatibility
nest_asyncio.apply()

# --- FLASK SERVER (To keep the bot alive on Render) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "SwiftFakeMailBot is running!", 200

def run_flask():
    # Render uses port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- BOT CONFIGURATION ---
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8427226244:AAG9sDCHxaQm3IcRjzQimz0MTcEmOr_dvd0"

app = Client("SwiftFakeMailBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# In-memory user data
user_data = {} 
DOMAINS = ["1secmail.com", "1secmail.org", "1secmail.net"]

# --- UTILITY FUNCTIONS ---
def clean_html(raw_html):
    if not raw_html: return "No content"
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n")

async def monitor_inbox(client, chat_id, email):
    """Background task to check for new emails every 8 seconds."""
    user, domain = email.split("@")
    seen_ids = set()
    
    # Pre-fetch existing emails to avoid double notifications
    try:
        init_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={user}&domain={domain}"
        init_msgs = requests.get(init_url).json()
        seen_ids = {m['id'] for m in init_msgs}
    except: pass

    while user_data.get(chat_id, {}).get("email") == email:
        try:
            url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={user}&domain={domain}"
            msgs = requests.get(url).json()
            
            for m in msgs:
                if m['id'] not in seen_ids:
                    seen_ids.add(m['id'])
                    # Fetch full message content
                    read_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={user}&domain={domain}&id={m['id']}"
                    full = requests.get(read_url).json()
                    
                    text = (
                        f"📩 **New Email Received!**\n\n"
                        f"📧 **To:** `{email}`\n"
                        f"👤 **From:** {m['from']}\n"
                        f"📝 **Subject:** {m['subject']}\n\n"
                        f"📄 **Content:**\n{clean_html(full['body'])[:3500]}"
                    )
                    await client.send_message(chat_id, text)
        except Exception as e:
            print(f"Monitoring Error: {e}")
            
        await asyncio.sleep(8)

# --- BOT HANDLERS ---
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    uid = message.from_user.id
    if uid not in user_data: user_data[uid] = {"domain": DOMAINS[0]}
    
    welcome = (
        "⚡️ **Swift Fake Mail Bot**\n\n"
        "Generate disposable email addresses instantly to stay safe from spam.\n\n"
        "• **Auto-Refresh:** Enabled ✅\n"
        "• **Custom Username:** Type any text to set it as your email name."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Random Email", callback_data="gen_rand")],
        [InlineKeyboardButton("🌐 Switch Domain", callback_data="list_dom")],
        [InlineKeyboardButton("🖼 Get QR Code", callback_data="qr_gen")]
    ])
    await message.reply(welcome, reply_markup=buttons)

@app.on_message(filters.text & filters.private)
async def handle_custom_name(client, message):
    uid = message.from_user.id
    if message.text.startswith("/"): return
    
    custom_name = "".join(e for e in message.text if e.isalnum()).lower()
    if not custom_name:
        return await message.reply("❌ Invalid name. Use only letters and numbers.")

    domain = user_data.get(uid, {}).get("domain", DOMAINS[0])
    email = f"{custom_name}@{domain}"
    
    user_data[uid]["email"] = email
    await message.reply(f"✅ **Email Set:** `{email}`\nMonitoring for messages... 📬")
    asyncio.create_task(monitor_inbox(client, uid, email))

@app.on_callback_query()
async def cb_handler(client, query):
    uid = query.from_user.id
    data = query.data

    if data == "gen_rand":
        domain = user_data.get(uid, {}).get("domain", DOMAINS[0])
        res = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1").json()
        email = res[0].split("@")[0] + "@" + domain
        user_data[uid]["email"] = email
        await query.message.edit_text(f"✅ **Generated:** `{email}`\nWaiting for mail... ⏳")
        asyncio.create_task(monitor_inbox(client, uid, email))

    elif data == "list_dom":
        btns = [[InlineKeyboardButton(d, callback_data=f"set_{d}")] for d in DOMAINS]
        await query.message.edit_text("Select an extension:", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("set_"):
        new_d = data.split("_")[1]
        user_data[uid]["domain"] = new_d
        await query.answer(f"Domain set to {new_d}")
        await start_cmd(client, query.message)

    elif data == "qr_gen":
        email = user_data.get(uid, {}).get("email")
        if not email: return await query.answer("Generate an email first!", show_alert=True)
        img = qrcode.make(email); buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
        await query.message.reply_photo(buf, caption=f"QR Code for: {email}")

# --- STARTUP LOGIC ---
async def start_bot():
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("SwiftFakeMailBot is starting...")
    await app.start()
    print("Bot is now ONLINE!")
    await asyncio.Future() # Keep alive

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
