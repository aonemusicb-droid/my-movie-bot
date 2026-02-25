import telebot
import firebase_admin
from firebase_admin import credentials, db

# 1. Firebase Setup
# 'serviceAccountKey.json' എന്ന ഫയൽ ഇതേ ഫോൾഡറിൽ ഉണ്ടെന്ന് ഉറപ്പുവരുത്തുക
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://efootball-market-9e735-default-rtdb.firebaseio.com'
})

# 2. നിങ്ങൾ നൽകിയ ബോട്ട് വിവരങ്ങൾ ഇവിടെ ചേർത്തിരിക്കുന്നു
BOT_TOKEN = '8638140599:AAHVKV85DUO4M666Mrwz9O1eUcN292hc_gE'
# ശ്രദ്ധിക്കുക: API Hash, API Key എന്നിവ സാധാരണയായി ബോട്ട് റൺ ചെയ്യാൻ ഈ കോഡിൽ ആവശ്യമില്ല.
# അവ 'UserBot' ഉണ്ടാക്കാൻ മാത്രമാണ് ഉപയോഗിക്കുന്നത്.

# നിങ്ങളുടെ ടെലിഗ്രാം ID ഇവിടെ നൽകുക (ഉദാഹരണത്തിന്: 123456789)
# @userinfobot വഴി ഇത് കണ്ടെത്താം
ADMIN_ID = 123456789 

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome! Type movie name to search.")

# സിനിമ ചേർക്കാൻ: /add Movie Name | Link
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only!")
        return
    try:
        data = message.text.split('/add ')[1]
        name, link = data.split('|')
        ref = db.reference('movies')
        ref.push({
            'search_name': name.strip().lower(),
            'display_name': name.strip(),
            'link': link.strip()
        })
        bot.reply_to(message, f"✅ Added: {name}")
    except:
        bot.reply_to(message, "Use format: /add Movie | Link")

@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.lower().strip()
    ref = db.reference('movies')
    movies = ref.get()
    if movies:
        for key, value in movies.items():
            if query in value['search_name']:
                bot.reply_to(message, f"🎬 {value['display_name']}\n🔗 {value['link']}")
                return
    bot.reply_to(message, "🔍 Not found!")

print("Bot is starting...")
bot.polling()
