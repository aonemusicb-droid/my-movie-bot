import telebot
import firebase_admin
from firebase_admin import credentials, db

# --- 1. CONFIGURATION ---
BOT_TOKEN = '8639239835:AAFMaP9CodJJyiaJ6dugIRo03sY-kcf-GmY'
DATABASE_URL = 'https://efootball-market-9e735-default-rtdb.firebaseio.com'
ADMIN_ID = 123456789 # നിങ്ങളുടെ ടെലിഗ്രാം ഐഡി ഇവിടെ നൽകുക

# --- 2. FIREBASE INITIALIZATION ---
# പഴയ Error ഒഴിവാക്കാൻ Firebase സെറ്റിംഗ്സ് ശ്രദ്ധിക്കുക
if not firebase_admin._apps:
    # serviceAccountKey.json ഫയൽ Render-ൽ ഉണ്ടെന്ന് ഉറപ്പുവരുത്തുക
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. AUTO-INDEXING LOGIC ---
# നിങ്ങൾ ചാനലിൽ സിനിമ ഇടുമ്പോൾ അത് തനിയെ ഡാറ്റാബേസിൽ സേവ് ചെയ്യും
@bot.channel_post_handler(content_types=['document', 'video'])
def auto_index_channel(message):
    movie_name = message.caption if message.caption else message.document.file_name
    if movie_name:
        ref = db.reference('movies')
        ref.push({
            'name': movie_name.lower().strip(),
            'display_name': movie_name,
            'msg_id': message.message_id,
            'chat_id': message.chat.id
        })
        print(f"✅ Indexed: {movie_name}")

# --- 4. SEARCH LOGIC ---
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.lower().strip()
    ref = db.reference('movies')
    all_movies = ref.get()

    if all_movies:
        for key, value in all_movies.items():
            if query in value['name']:
                # ചാനലിൽ നിന്ന് നേരിട്ട് കോപ്പി ചെയ്ത് അയക്കുന്നു
                try:
                    bot.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=value['chat_id'],
                        message_id=value['msg_id']
                    )
                    return
                except Exception as e:
                    bot.reply_to(message, "⚠️ Error: ചാനലിൽ ബോട്ടിനെ അഡ്മിൻ ആക്കിയിട്ടുണ്ടോ?")
                    return

    bot.reply_to(message, "🔍 ആ സിനിമ കണ്ടെത്താനായില്ല. സ്പെല്ലിംഗ് ശ്രദ്ധിക്കുക!")

if __name__ == "__main__":
    print("🚀 Auto-Indexing Bot is Live...")
    bot.infinity_polling()
