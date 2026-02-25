import telebot
from supabase import create_client, Client

# --- CONFIGURATION ---
BOT_TOKEN = '8638140599:AAHVKV85DUO4M666Mrwz9O1eUcN292hc_gE'
SUPABASE_URL = "https://qnduzsrrmuobxqlbjcgs.supabase.co"
SUPABASE_KEY = "Sb_publishable_jwwUEC4KCOZHVd_oaJm0_g_ejFKyHId"

bot = telebot.TeleBot(BOT_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 1. AUTO INDEXING (ചാനലിൽ സിനിമ ഇടുമ്പോൾ) ---
@bot.channel_post_handler(content_types=['document', 'video'])
def auto_index(message):
    # ഫയൽ നെയിം അല്ലെങ്കിൽ ക്യാപ്ഷൻ എടുക്കുന്നു
    movie_name = message.caption if message.caption else (message.document.file_name if message.document else "Unknown")
    
    data = {
        "name": movie_name.lower().strip(),
        "msg_id": message.message_id,
        "chat_id": message.chat.id
    }
    
    # Supabase-ലേക്ക് സേവ് ചെയ്യുന്നു
    try:
        supabase.table("movies").insert(data).execute()
        print(f"✅ Indexed: {movie_name}")
    except Exception as e:
        print(f"❌ Database Error: {e}")

# --- 2. SEARCH LOGIC (യൂസർ സെർച്ച് ചെയ്യുമ്പോൾ) ---
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.lower().strip()
    
    # ഡാറ്റാബേസിൽ സെർച്ച് ചെയ്യുന്നു (Partial match)
    try:
        response = supabase.table("movies").select("*").ilike("name", f"%{query}%").execute()
        movies = response.data

        if movies:
            for movie in movies:
                bot.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=movie['chat_id'],
                    message_id=movie['msg_id']
                )
            return
        else:
            bot.reply_to(message, "🔍 Sorry, movie not found!")
    except Exception as e:
        bot.reply_to(message, "⚠️ Something went wrong with the database.")
        print(f"Search Error: {e}")

if __name__ == "__main__":
    print("🚀 Bot is running with Supabase...")
    bot.infinity_polling()
