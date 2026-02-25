import telebot
import logging

# 1. Configuration
# Replace with your actual Bot Token
BOT_TOKEN = '8638140599:AAHVKV85DUO4M666Mrwz9O1eUcN292hc_gE'
bot = telebot.TeleBot(BOT_TOKEN)

# 2. Movie Database (Dictionary)
# Professional way to store data within the code
MOVIE_DATABASE = {
    "manjummel boys": "https://t.me/searchmymoviedata/10",
    "premalu": "https://t.me/searchmymoviedata/11",
    "avesham": "https://t.me/searchmymoviedata/12",
    "bramayugam": "https://t.me/searchmymoviedata/13"
}

# 3. Logging for Debugging
logging.basicConfig(level=logging.INFO)

# --- COMMAND HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"Hello {user_name}! 👋\n\n"
        "Welcome to **Movie Search Bot**.\n"
        "Send me a movie name to get the link.\n\n"
        "📢 Join: @searchmymovieupdate"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# --- SEARCH LOGIC ---

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    query = message.text.lower().strip()
    logging.info(f"User searched for: {query}")

    if query in MOVIE_DATABASE:
        download_link = MOVIE_DATABASE[query]
        response = (
            f"🎬 **Movie Found!**\n\n"
            f"📌 **Name:** {query.capitalize()}\n"
            f"🔗 **Link:** [Click Here to Download]({download_link})\n\n"
            f"🔰 Enjoy your movie!"
        )
        bot.reply_to(message, response, parse_mode='Markdown', disable_web_page_preview=False)
    else:
        not_found_text = (
            "🔍 **Sorry, Movie Not Found!**\n\n"
            "Please check the spelling or try another movie.\n"
            "Request movies here: @searchmymoviedata"
        )
        bot.reply_to(message, not_found_text, parse_mode='Markdown')

# 4. Bot Polling
if __name__ == "__main__":
    print("🚀 Bot is starting professionally...")
    bot.infinity_polling()
