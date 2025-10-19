from flask import Flask, request
import requests
import telebot
import os

# --- Your bot token ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/tokens/"
TOKEN_ADDRESS = "ap5cyvzjbqliw5lq8zaynnsygbdeddxvcwqanxahwojx"  # change this to your token address


def get_token_price():
    try:
        response = requests.get(DEXSCREENER_URL + TOKEN_ADDRESS)
        data = response.json()
        if "pairs" in data and len(data["pairs"]) > 0:
            pair = data["pairs"][0]
            price_usd = pair["priceUsd"]
            pair_name = pair["baseToken"]["symbol"] + "/" + pair["quoteToken"]["symbol"]
            return f"{pair_name} price: ${float(price_usd):,.6f}"
        else:
            return "⚠️ Token not found on DexScreener."
    except Exception as e:
        return f"Error fetching price: {e}"


@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    bot.reply_to(message, "👋 Welcome!\n\nCommands:\n/price — Get latest token price instantly.")


@bot.message_handler(commands=['price'])
def send_price(message):
    price = get_token_price()
    bot.reply_to(message, price)


# --- Flask route for webhook ---
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200


# --- Home route ---
@app.route('/')
def home():
    return "Bot is running perfectly!", 200


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Webhook setup for Render
    PORT = int(os.environ.get('PORT', 5000))
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}")

    app.run(host="0.0.0.0", port=PORT)