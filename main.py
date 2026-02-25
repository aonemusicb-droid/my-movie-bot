import telebot
import firebase_admin
from firebase_admin import credentials, db
import os

# --- 1. CONFIGURATION ---
# നിങ്ങളുടെ വിവരങ്ങൾ ഇവിടെ നൽകുക
BOT_TOKEN = '8638140599:AAHVKV85DUO4M666Mrwz9O1eUcN292hc_gE'
ADMIN_ID = 123456789  # <--- നിങ്ങളുടെ ടെലിഗ്രാം ഐഡി ഇവിടെ മാറ്റുക
DATABASE_URL = 'https://efootball-market-9e735-default-rtdb.firebaseio.com'

# --- 2. FIREBASE INITIALIZATION ---
try:
    # 'serviceAccountKey.json' സെർവറിലുണ്ടോ എന്ന് പരിശോധിക്കുന്നു
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': DATABASE_URL
        })
        print("✅ Firebase Connected Successfully!")
    else:
        print("❌ Error: serviceAccountKey.json not found!")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. BOT COMMANDS ---

# /start കമാൻഡ്
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to Movie Finder!**\n\n"
        "സിനിമയുടെ പേര് അയച്ചു നൽകിയാൽ ഡൗൺലോഡ് ലിങ്ക് ലഭിക്കും.\n\n"
        "📢 Join: @searchmymoviedata"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# അഡ്മിന് സിനിമ ആഡ് ചെയ്യാനുള്ള കമാൻഡ്
# Format: /add Movie Name | Link
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⚠️ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അനുവാദമില്ല.")
        return

    try:
        # സിനിമയുടെ പേരും ലിങ്കും വേർതിരിക്കുന്നു
        raw_data = message.text.split('/add ')[1]
        movie_name, movie_link = raw_data.split('|')
        
        ref = db.reference('movies')
        ref.push({
            'search_name': movie_name.strip().lower(),
            'display_name': movie_name.strip(),
            'link': movie_link.strip()
        })
        bot.reply_to(message, f"✅ സിനിമ വിജയകരമായി ആഡ് ചെയ്തു:\n**{movie_name.strip()}**", parse_mode='Markdown')
    except Exception:
        bot.reply_to(message, "❌ തെറ്റായ രീതി! \n\nഉപയോഗിക്കേണ്ട വിധം:\n`/add Pulimurugan | https://t.me/example`", parse_mode='Markdown')

# സെർച്ച് ലോജിക്
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.lower().strip()
    ref = db.reference('movies')
    all_movies = ref.get()
    
    found = False
    if all_movies:
        for key, value in all_movies.items():
            if query in value['search_name']:
                response = (
                    f"🎬 **{value['display_name']}**\n\n"
                    f"🔗 **Download Link:** {value['link']}\n\n"
                    f"🔰 Shared by @searchmymoviedata"
                )
                bot.reply_to(message, response, parse_mode='Markdown')
                found = True
                break # ആദ്യത്തെ റിസൾട്ട് കിട്ടുമ്പോൾ നിർത്താൻ
    
    if not found:
        bot.reply_to(message, "🔍 ക്ഷമിക്കണം, ആ സിനിമ കണ്ടെത്താനായില്ല. സ്പെല്ലിംഗ് പരിശോധിക്കുക.")

# ബോട്ട് റൺ ചെയ്യുന്നു
print("🚀 Bot is live...")
bot.infinity_polling()
