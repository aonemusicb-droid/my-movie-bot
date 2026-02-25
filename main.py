import telebot
from supabase import create_client, Client
import logging

# --- 1. CONFIGURATION ---
BOT_TOKEN = '8638140599:AAEv8pqLb0Ag-uLtmGo3Yr0uaKebNcw89CA'
SUPABASE_URL = "https://qnduzsrrmuobxqlbjcgs.supabase.co"
SUPABASE_KEY = "Sb_publishable_jwwUEC4KCOZHVd_oaJm0_g_ejFKyHId"

bot = telebot.TeleBot(BOT_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(level=logging.INFO)

# --- 2. START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello! Send me a movie name and I will find the file for you.")

# --- 3. AUTO INDEXING (ചാനലിൽ മൂവി ഇടുമ്പോൾ സേവ് ചെയ്യാൻ) ---
@bot.channel_post_handler(content_types=['document', 'video'])
def auto_index(message):
    try:
        # ഫയൽ നെയിം അല്ലെങ്കിൽ ക്യാപ്ഷൻ എടുക്കുന്നു
        movie_name = ""
        if message.caption:
            movie_name = message.caption
        elif message.document:
            movie_name = message.document.file_name
        elif message.video:
            movie_name = "New Movie File" # വീഡിയോയ്ക്ക് പേര് ഇല്ലെങ്കിൽ

        data = {
            "name": movie_name.lower().strip(),
            "msg_id": message.message_id,
            "chat_id": message.chat.id
        }
        
        # Supabase-ലേക്ക് ഇൻസേർട്ട് ചെയ്യുന്നു
        supabase.table("movies").insert(data).execute()
        logging.info(f"✅ Indexed successfully: {movie_name}")
    except Exception as e:
        logging.error(f"❌ Indexing Error: {e}")

# --- 4. SEARCH LOGIC ---
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.lower().strip()
    
    try:
        # ഡാറ്റാബേസിൽ നിന്ന് എല്ലാ സിനിമകളും എടുക്കുന്നു
        response = supabase.table("movies").select("*").execute()
        movies = response.data

        found = False
        if movies:
            for movie in movies:
                # പേര് മാച്ച് ആകുന്നുണ്ടോ എന്ന് നോക്കുന്നു
                if query in movie['name'].lower():
                    try:
                        bot.copy_message(
                            chat_id=message.chat.id,
                            from_chat_id=movie['chat_id'],
                            message_id=movie['msg_id']
                        )
                        found = True
                    except Exception as e:
                        logging.error(f"Copy Error: {e}")

        if not found:
            bot.reply_to(message, "🔍 Sorry, movie not found! Make sure you have uploaded it to the channel after starting the bot.")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ Database Error: {str(e)}")
        logging.error(f"Full Error: {e}")

if __name__ == "__main__":
    print("🚀 Bot is running with Supabase Auto-Filter...")
    bot.infinity_polling(skip_pending=True)
