import telebot
from supabase import create_client, Client
import logging

# --- 1. CONFIGURATION ---
# Replace with your actual credentials if they change
BOT_TOKEN = '8638140599:AAEv8pqLb0Ag-uLtmGo3Yr0uaKebNcw89CA'
SUPABASE_URL = "https://qnduzsrrmuobxqlbjcgs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFuZHV6c3JybXVvYnhxbGJqY2dzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5ODY2NTEsImV4cCI6MjA4NzU2MjY1MX0.hkCBL14oYSuBqPsHHAyuHWgbGFo8GAkiCbVThlVA5dg"

bot = telebot.TeleBot(BOT_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Enable Logging to track errors in Render/Terminal
logging.basicConfig(level=logging.INFO)

# --- 2. START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to the Movie Search Bot!**\n\n"
        "I can help you find movies from the connected channel.\n\n"
        "🔹 **How to use:** Just type the name of the movie.\n"
        "🔹 **Note:** I only index new movies uploaded to the channel after I was added as an Admin."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# --- 3. AUTO INDEXING (Saves new channel posts to Database) ---
@bot.channel_post_handler(content_types=['document', 'video'])
def auto_index(message):
    try:
        # Determine the movie name from caption or file name
        movie_name = ""
        if message.caption:
            movie_name = message.caption
        elif message.document:
            movie_name = message.document.file_name
        elif message.video:
            movie_name = "Unnamed Video File"

        # Prepare data for Supabase
        data = {
            "name": movie_name.lower().strip(),
            "msg_id": message.message_id,
            "chat_id": message.chat.id
        }
        
        # Insert data into 'movies' table
        supabase.table("movies").insert(data).execute()
        logging.info(f"✅ Successfully Indexed: {movie_name}")
        
    except Exception as e:
        logging.error(f"❌ Indexing Error: {e}")

# --- 4. SEARCH LOGIC (Finds movie from Database) ---
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.lower().strip()
    logging.info(f"User is searching for: {query}")
    
    try:
        # Fetch all movies from the database
        response = supabase.table("movies").select("*").execute()
        movies = response.data

        found = False
        if movies:
            for movie in movies:
                # Check if search query exists in movie name
                if query in movie['name'].lower():
                    try:
                        # Copy the message from the channel to the user
                        bot.copy_message(
                            chat_id=message.chat.id,
                            from_chat_id=movie['chat_id'],
                            message_id=movie['msg_id']
                        )
                        found = True
                    except Exception as e:
                        logging.error(f"Forwarding Error: {e}")

        if not found:
            bot.reply_to(message, "🔍 **Movie not found!**\n\nPlease check the spelling or ensure the movie has been uploaded to the channel.")
            
    except Exception as e:
        bot.reply_to(message, "⚠️ **Database connection error!**\n\nPlease ensure RLS is disabled in Supabase settings.")
        logging.error(f"Search Error: {e}")

# --- 5. RUN THE BOT ---
if __name__ == "__main__":
    print("🚀 Bot is running...")
    bot.infinity_polling(skip_pending=True)
