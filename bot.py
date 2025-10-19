import requests
import telebot
from telebot import types

# 🔐 Replace this with your new Telegram Bot Token
BOT_TOKEN = "7004858190:AAFTOL_ll9ta99ReyW_kYUbzT0VP6gR7M2A"

bot = telebot.TeleBot(BOT_TOKEN)

# 🏁 Command: /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Hey 👋 I'm your Crypto Forecast Bot!\n"
        "Type /price to get the latest coin price 💰"
    )

# 💰 Command: /price
@bot.message_handler(commands=['price'])
def get_price(message):
    try:
        url = f"https://dexscreener.com/solana/ap5cyvzjbqliw5lq8zaynnsygbdeddxvcwqanxahwojx"
        response = requests.get(url)
        data = response.json()

        if "pairs" in data and len(data["pairs"]) > 0:
            pair = data["pairs"][0]
            base_token = pair["baseToken"]["symbol"]
            quote_token = pair["quoteToken"]["symbol"]
            price_usd = pair["priceUsd"]
            price_native = pair["priceNative"]
            volume_24h = pair["volume"]["h24"]
            liquidity_usd = pair["liquidity"]["usd"]

            reply = (
                f"📊 <b>{base_token}/{quote_token}</b>\n"
                f"💵 Price (USD): ${price_usd}\n"
                f"💰 Native Price: {price_native}\n"
                f"📈 24h Volume: ${volume_24h}\n"
                f"💧 Liquidity: ${liquidity_usd}\n"
                f"\nSource: Dexscreener"
            )
        else:
            reply = "⚠️ Couldn’t fetch data. Check the CA or try again later."

        bot.send_message(message.chat.id, reply, parse_mode="HTML")

    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# 📢 Default message (for anything else)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Try /price to check live coin info 💰")

if __name__ == "__main__":
    print("🚀 Bot is now running on Render!")
    bot.polling(none_stop=True)
