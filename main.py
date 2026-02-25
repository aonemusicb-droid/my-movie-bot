import telebot
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
# Replace with your actual bot token from @BotFather
BOT_TOKEN = '8639239835:AAHWk0Rjk0IomZV3BMDF0KgxWS4-jwzQasw'

# Supabase Credentials
SUPABASE_URL = "https://qnduzsrrmuobxqlbjcgs.supabase.co"
SUPABASE_KEY = "Sb_publishable_jwwUEC4KCOZHVd_oaJm0_g_ejFKyHId"

# --- 2. INITIALIZATION ---
# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. AUTO-INDEXING (Save movies from channel) ---
@bot.channel_post_handler(content_types=['document', 'video'])
def auto_index_channel(message):
    movie_name = ""
    
    # Extract file name or caption
    if message.document:
        movie_name = message.caption if message.caption else message.document.file_name
    elif message.video:
        movie_name = message.caption if message.caption else "Unknown Video"
    
    if movie_name:
        data = {
            "name": movie_name.lower().strip(),
            "msg_id": message.message_id,
            "chat_id": message.chat.id
        }
        try:
            # Insert data into Supabase 'movies' table
            supabase.table("movies").insert(data).execute()
            print(f"✅ Successfully Indexed: {movie_name}")
        except Exception as e:
            print(f"❌ Database Error: {e}")

# --- 4. SEARCH LOGIC (Send movies to users) ---
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.lower().strip()
    
    try:
        # Search for the movie name using partial match (ilike)
        response = supabase.table("movies").select("*").ilike("name", f"%{query}%").execute()
        results = response.data
        
        if results:
            for movie in results:
                try:
                    # Copy the message from the channel to the user
                    bot.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=movie['chat_id'],
                        message_id=movie['msg_id']
                    )
                except Exception as e:
                    bot.reply_to(message, "⚠️ Error: Make sure the bot is an Admin in the channel.")
                    break
        else:
            bot.reply_to(message, "🔍 Movie not found! Please check the spelling.")
            
    except Exception as e:
        bot.reply_to(message, "⚠️ Database Error: Ensure the 'movies' table is created correctly.")
        print(f"Search Error: {e}")

# --- 5. START THE BOT ---
if __name__ == "__main__":
    print("🚀 Bot is running...")
    bot.infinity_polling()
