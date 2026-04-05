import asyncio
import logging
import sys

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)

# Config va Database
from config import BOT_TOKEN
import database as db

# Handlers
from handlers.start import registration_conv
from handlers.elonlar import (
    elon_conv, buyurtma_berish_menu, my_ads_menu,
    ad_detail_callback, my_ad_view_callback, delete_ad_callback,
)
from handlers.buyurtma import order_conv, my_orders_menu
from handlers.subscription import subscription_menu, sub_conv
from handlers.usta import usta_menu, about_menu
from handlers.admin import (
    admin_command, admin_panel_button, admin_callback,
    order_action_callback, sub_action_callback, set_role_callback,
)

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def start_bot():
    try:
        # 1. Ma'lumotlar bazasini tekshirish
        logger.info("⏳ Ma'lumotlar bazasi ulanmoqda...")
        try:
            await db.init_db()
            logger.info("✅ Baza muvaffaqiyatli ulandi.")
        except Exception as db_err:
            logger.error(f"❌ Baza ulanishida xato: {db_err}")

        # 2. Application builder
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN topilmadi! Config faylni tekshiring.")
            return

        app = Application.builder().token(BOT_TOKEN).build()

        # ── Handlers qo'shish ──────────────────────────────────────────
        
        # Conversation handlers (Bular birinchi turishi kerak)
        app.add_handler(registration_conv)
        app.add_handler(elon_conv)
        app.add_handler(sub_conv)
        app.add_handler(order_conv)

        # Message handlers (Asosiy menyu tugmalari)
        app.add_handler(MessageHandler(filters.Regex("^🛒 Buyurtma berish$"), buyurtma_berish_menu))
        app.add_handler(MessageHandler(filters.Regex("^👤 E'lonlarim$"), my_ads_menu))
        app.add_handler(MessageHandler(filters.Regex("^📋 Buyurtmalarim$"), my_orders_menu))
        app.add_handler(MessageHandler(filters.Regex("^💎 Obuna$"), subscription_menu))
        app.add_handler(MessageHandler(filters.Regex("^🔧 Usta topish$"), usta_menu))
        app.add_handler(MessageHandler(filters.Regex("^ℹ️ Bot haqida$"), about_menu))
        app.add_handler(MessageHandler(filters.Regex("^🛡 Admin panel$"), admin_panel_button))

        # Commands
        app.add_handler(CommandHandler("admin", admin_command))

        # Callback query handlers (Inline tugmalar uchun)
        # DIQQAT: Patternlar keyboards.py dagi callback_data ga moslandi
        app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
        app.add_handler(CallbackQueryHandler(ad_detail_callback, pattern="^ad_view_")) # ad_view_{id}
        app.add_handler(CallbackQueryHandler(my_ad_view_callback, pattern="^myad_view_")) # myad_view_{id}
        app.add_handler(CallbackQueryHandler(delete_ad_callback, pattern="^del_ad_"))
        app.add_handler(CallbackQueryHandler(order_action_callback, pattern="^ord_(ok|rej)_"))
        app.add_handler(CallbackQueryHandler(sub_action_callback, pattern="^sub_(app|rej)_"))
        app.add_handler(CallbackQueryHandler(set_role_callback, pattern="^role_"))

        logger.info("🚀 Bot polling rejimida ishga tushmoqda...")
        
        # 3. Railway va lokal uchun start
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Botni ushlab turish
        await asyncio.Event().wait()

    except Exception as e:
        logger.critical(f"💥 Bot ishga tushishida jiddiy xato: {e}", exc_info=True)
    finally:
        await db.close_db()

if __name__ == "__main__":
    try:
        async def main():
            await start_bot()
        
        # Windowsda 'Event loop is closed' xatosi chiqmasligi uchun
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Bot to'xtatildi!")