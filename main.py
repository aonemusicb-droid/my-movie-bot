import telebot

# --- CONFIGURATION ---
BOT_TOKEN = '8638140599:AAEFmtIRHqvUIEqYV4fIChG8vavTtoyIPzM'
# നിങ്ങളുടെ ചാനൽ ID (ഉദാ: -1002345678901)
CHANNEL_ID = -1002345678901 

bot = telebot.TeleBot(BOT_TOKEN)

# ശ്രദ്ധിക്കുക: ഡാറ്റാബേസ് ഇല്ലാതെ ചാനലിലെ എല്ലാ ഫയലുകളും സെർച്ച് ചെയ്യാൻ 
# ബോട്ടിന് ചാനലിലെ മെസ്സേജുകളുടെ ഒരു ലിസ്റ്റ് ആവശ്യമാണ്.
# തുടക്കത്തിൽ നമുക്ക് പ്രധാന സിനിമകൾ ഒരു ലിസ്റ്റായി നൽകാം.

MOVIES = {
    "sumathi valavu": 10,  # 10 എന്നത് ചാനലിലെ മെസ്സേജ് ID ആണ്
    "avesham": 12,
    "manjummel boys": 15
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hello! Send me the movie name.")

@bot.message_handler(func=lambda message: True)
def auto_search(message):
    query = message.text.lower().strip()
    
    # യൂസർ അയച്ച പേര് ലിസ്റ്റിൽ ഉണ്ടോ എന്ന് നോക്കുന്നു
    found = False
    for name, msg_id in MOVIES.items():
        if query in name:
            try:
                # ചാനലിൽ നിന്ന് നേരിട്ട് ആ ഫയൽ കോപ്പി ചെയ്ത് അയക്കുന്നു
                bot.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id
                )
                found = True
                break
            except Exception as e:
                print(f"Error: {e}")

    if not found:
        bot.reply_to(message, "🔍 ചാനലിൽ ആ സിനിമ കണ്ടെത്താനായില്ല!")

bot.infinity_polling()
