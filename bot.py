import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)

from config import BOT_TOKEN
import database as db

# Handlers (Fayl manzillari to'g'riligiga ishonch hosil qiling)
from handlers.start import registration_conv
from handlers.elonlar import (
    elon_conv,
    buyurtma_berish_menu,
    my_ads_menu,
    ad_detail_callback,
    my_ad_view_callback,
    delete_ad_callback,
)
from handlers.buyurtma import order_conv, my_orders_menu
from handlers.subscription import subscription_menu, sub_conv
from handlers.usta import usta_menu, about_menu
from handlers.admin import (
    admin_command,
    admin_panel_button,
    admin_callback,
    order_action_callback,
    sub_action_callback,
    set_role_callback,
)

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def start_bot():
    # 1. Ma'lumotlar bazasini ishga tushirish
    await db.init_db()
    
    # 2. Application builder
    app = Application.builder().token(BOT_TOKEN).build()

    # ── ConversationHandlers (ustuvorlik tartibi) ──────────────────────────
    app.add_handler(registration_conv)      # /start + ro'yxatdan o'tish
    app.add_handler(elon_conv)              # E'lon berish
    app.add_handler(sub_conv)               # Obuna to'lov cheki
    app.add_handler(order_conv)             # Buyurtma berish

    # ── Oddiy xabar handlerlari ───────────────────────────────────────────
    app.add_handler(MessageHandler(filters.Regex("^🛒 Buyurtma berish$"), buyurtma_berish_menu))
    app.add_handler(MessageHandler(filters.Regex("^👤 E'lonlarim$"), my_ads_menu))
    app.add_handler(MessageHandler(filters.Regex("^📋 Buyurtmalarim$"), my_orders_menu))
    app.add_handler(MessageHandler(filters.Regex("^💎 Obuna$"), subscription_menu))
    app.add_handler(MessageHandler(filters.Regex("^🔧 Usta topish$"), usta_menu))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Bot haqida$"), about_menu))
    app.add_handler(MessageHandler(filters.Regex("^🛡 Admin panel$"), admin_panel_button))

    # ── Admin buyrug'i ───────────────────────────────────────────────────
    app.add_handler(CommandHandler("admin", admin_command))

    # ── Inline callback handlerlari ──────────────────────────────────────
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(ad_detail_callback, pattern="^ad_\\d+$"))
    app.add_handler(CallbackQueryHandler(my_ad_view_callback, pattern="^myadview_"))
    app.add_handler(CallbackQueryHandler(delete_ad_callback, pattern="^del_ad_"))
    app.add_handler(CallbackQueryHandler(order_action_callback, pattern="^ord_(ok|rej)_"))
    app.add_handler(CallbackQueryHandler(sub_action_callback, pattern="^sub_(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(set_role_callback, pattern="^role_"))

    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
    
    # 3. Botni asinxron ishga tushirish
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        # Botni to'xtamaguncha ushlab turish
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        # Windows'da event loop muammosini hal qilish uchun
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("❌ Bot to'xtatildi!")