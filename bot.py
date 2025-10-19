import requests
import time
import json

# ================= CONFIG =================
TELEGRAM_TOKEN = "7004858190:AAH5klemWBzLw4RwKjGkBoQtx_Yst-ZpBjk" # Replace with your bot token
UPDATE_INTERVAL = 60  # Check every 60 seconds for instant alerts
SUBSCRIPTIONS_FILE = "subscriptions.json"
ALERTS_FILE = "alerts.json"

# DexScreener pool for Solmello
COINS = {
    "solmello": "solana/AP5cyVzjbQLiw5LQ8zAynnSygbDeDDXvCWQANXahWojx"
}
# ==========================================

# Load or initialize subscriptions
try:
    with open(SUBSCRIPTIONS_FILE, "r") as f:
        subscriptions = json.load(f)
except:
    subscriptions = {}

# Load or initialize alerts
try:
    with open(ALERTS_FILE, "r") as f:
        alerts = json.load(f)
except:
    alerts = {}

# Send Telegram message
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Send message error:", e)

# Fetch price from DexScreener
def get_price(coin_id):
    pair = COINS.get(coin_id)
    if not pair:
        return None, None
    url = f"https://api.dexscreener.com/latest/dex/pairs/{pair}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = float(data["pair"]["priceUsd"])
        change = float(data["pair"]["priceChange"]["h24"])
        return price, change
    except Exception as e:
        print(f"Price fetch error {coin_id}:", e)
        return None, None

# Handle Telegram messages
def handle_message(update):
    chat_id = str(update["message"]["chat"]["id"])
    text = update["message"].get("text", "").lower()

    if text.startswith("/price"):
        parts = text.split()
        coin = parts[1] if len(parts) > 1 else "solmello"
        price, change = get_price(coin)
        if price is not None:
            emoji = "🔺" if change >= 0 else "🔻"
            msg = f"{coin.title()}\nPrice: ${price:.6f}\n24h: {emoji} {change:.2f}%"
        else:
            msg = f"⚠️ Could not fetch {coin} price."
        send_message(chat_id, msg)

    elif text.startswith("/subscribe"):
        parts = text.split()
        if len(parts) > 1:
            coin = parts[1]
            if coin not in COINS:
                send_message(chat_id, f"⚠️ {coin} not supported.")
                return
            subscriptions.setdefault(chat_id, [])
            if coin not in subscriptions[chat_id]:
                subscriptions[chat_id].append(coin)
                send_message(chat_id, f"Subscribed to {coin} updates!")
            else:
                send_message(chat_id, f"Already subscribed to {coin}.")
            with open(SUBSCRIPTIONS_FILE, "w") as f:
                json.dump(subscriptions, f)

    elif text.startswith("/unsubscribe"):
        parts = text.split()
        if len(parts) > 1:
            coin = parts[1]
            if chat_id in subscriptions and coin in subscriptions[chat_id]:
                subscriptions[chat_id].remove(coin)
                send_message(chat_id, f"Unsubscribed from {coin}.")
                with open(SUBSCRIPTIONS_FILE, "w") as f:
                    json.dump(subscriptions, f)
            else:
                send_message(chat_id, f"You're not subscribed to {coin}.")

    elif text.startswith("/alert"):
        parts = text.split()
        if len(parts) == 3:
            coin, price_str = parts[1], parts[2]
            if coin not in COINS:
                send_message(chat_id, f"⚠️ {coin} not supported.")
                return
            try:
                price = float(price_str)
                alerts.setdefault(chat_id, {})
                alerts[chat_id][coin] = price
                send_message(chat_id, f"Alert set for {coin} at ${price}")
                with open(ALERTS_FILE, "w") as f:
                    json.dump(alerts, f)
            except:
                send_message(chat_id, "Invalid price format.")

    elif text.startswith("/help"):
        msg = (
            "/price <coin> - Get coin price\n"
            "/subscribe <coin> - Subscribe to updates\n"
            "/unsubscribe <coin> - Stop updates\n"
            "/alert <coin> <price> - Set instant price alert\n"
            "/help - Show this message"
        )
        send_message(chat_id, msg)

# Telegram getUpdates
OFFSET_FILE = "offset.txt"
try:
    with open(OFFSET_FILE, "r") as f:
        offset = int(f.read())
except:
    offset = 0

def get_updates():
    global offset
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?timeout=10&offset={offset+1}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if data["ok"]:
            for update in data["result"]:
                offset = update["update_id"]
                handle_message(update)
            with open(OFFSET_FILE, "w") as f:
                f.write(str(offset))
    except Exception as e:
        print("Update fetch error:", e)

# Send scheduled updates to subscribers
def send_scheduled_updates():
    coin_cache = {}
    for chat_id, coins in subscriptions.items():
        for coin in coins:
            if coin not in coin_cache:
                price, change = get_price(coin)
                coin_cache[coin] = (price, change)
            else:
                price, change = coin_cache[coin]
            if price is not None:
                emoji = "🔺" if change >= 0 else "🔻"
                msg = f"{coin.title()}\nPrice: ${price:.6f}\n24h: {emoji} {change:.2f}%"
                send_message(chat_id, msg)

# Check alerts instantly
def check_alerts():
    for chat_id, coin_alerts in list(alerts.items()):
        for coin, target in list(coin_alerts.items()):
            price, _ = get_price(coin)
            if price is not None and price >= target:
                send_message(chat_id, f"⚡ Alert! {coin.title()} price hit ${price}")
                alerts[chat_id].pop(coin)
                with open(ALERTS_FILE, "w") as f:
                    json.dump(alerts, f)

# ===== MAIN LOOP =====
while True:
    try:
        get_updates()
        send_scheduled_updates()
        check_alerts()
        time.sleep(UPDATE_INTERVAL)
    except Exception as e:
        print("Main loop error:", e)
        time.sleep(10)
