import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip()]
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@your_channel")
CARD_NUMBER = os.getenv("CARD_NUMBER", "8600 0000 0000 0000")
CARD_OWNER = os.getenv("CARD_OWNER", "To'lov qabul qiluvchi")

# Subscription plans
SUBSCRIPTION_PLANS = {
    "basic": {
        "name": "🥉 Boshlang'ich",
        "duration_days": 30,
        "price": 30000,
        "ads_limit": 5,
        "description": "30 kun | 5 ta e'lon | Asosiy imkoniyatlar",
    },
    "standard": {
        "name": "🥈 Standart",
        "duration_days": 30,
        "price": 60000,
        "ads_limit": 20,
        "description": "30 kun | 20 ta e'lon | Tezkor qo'llab-quvvatlash",
    },
    "premium": {
        "name": "🥇 Premium",
        "duration_days": 30,
        "price": 100000,
        "ads_limit": 999,
        "description": "30 kun | Cheksiz e'lon | Premium ustunlik",
    },
}
