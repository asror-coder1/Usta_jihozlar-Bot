from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
import database as db
from keyboards import (
    main_menu, cancel_kb, order_type_kb, confirm_kb, 
    order_manage_inline
)
from config import CARD_NUMBER, CARD_OWNER, ADMIN_IDS
from datetime import datetime

# States
ORD_AD_SEARCH, ORD_TYPE, ORD_CARD, ORD_CONFIRM = range(4)

# ─── BUYURTMA BERISH JARAYONI ────────────────────────────────────────────────

async def order_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline tugma: 'Buyurtma berish' — e'lon batafsilidan keladi"""
    query = update.callback_query
    await query.answer()

    # Pattern: order_start_{ad_id}
    parts = query.data.split("_")
    if len(parts) < 3: return
    
    ad_id = int(parts[2])
    ad = await db.get_ad(ad_id)
    if not ad:
        await query.edit_message_text("❌ E'lon topilmadi yoki o'chirilgan.")
        return

    context.user_data["order_ad_id"] = ad_id
    context.user_data["order_ad_title"] = ad["title"]
    context.user_data["order_ad_price"] = ad["price"]

    await query.message.reply_text(
        f"🛒 <b>Buyurtma berish</b>\n\n"
        f"📦 <b>{ad['title']}</b>\n"
        f"💰 Narx: {ad['price']}\n\n"
        "Qanday olishni tanlang:",
        parse_mode="HTML",
        reply_markup=order_type_kb(),
    )
    return ORD_TYPE


async def ord_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        return await ord_cancel(update, context)

    # Turini aniqlash
    context.user_data["order_type"] = "rent" if "Ijara" in text else "buy"
    type_label = "🔑 Ijaraga olish" if context.user_data["order_type"] == "rent" else "💳 Sotib olish"

    card_text = (
        f"💳 <b>To'lov bosqichi</b>\n\n"
        f"Buyurtma turi: <b>{type_label}</b>\n"
        f"Mahsulot: <b>{context.user_data.get('order_ad_title')}</b>\n\n"
        f"📌 To'lov kartasi:\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: <b>{CARD_OWNER}</b>\n\n"
        f"✅ To'lovni amalga oshiring va <b>chek rasmini</b> yuboring:"
    )
    await update.message.reply_text(card_text, parse_mode="HTML", reply_markup=cancel_kb())
    return ORD_CARD


async def ord_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.strip() == "❌ Bekor qilish":
        return await ord_cancel(update, context)

    photo = update.message.photo
    document = update.message.document
    file_id = None

    if photo:
        file_id = photo[-1].file_id
    elif document and document.mime_type.startswith("image/"):
        file_id = document.file_id
    else:
        await update.message.reply_text("❌ Iltimos, chek <b>rasmini</b> (yoki rasm faylini) yuboring:")
        return ORD_CARD

    context.user_data["order_card_photo"] = file_id
    
    ad_title = context.user_data.get("order_ad_title", "")
    ad_price = context.user_data.get("order_ad_price", "")
    type_label = "🔑 Ijaraga olish" if context.user_data.get("order_type") == "rent" else "💳 Sotib olish"

    await update.message.reply_text(
        f"📋 <b>Buyurtmani tasdiqlash</b>\n\n"
        f"📦 Mahsulot: <b>{ad_title}</b>\n"
        f"💰 Narx: <b>{ad_price}</b>\n"
        f"🏷 Turi: <b>{type_label}</b>\n\n"
        "Barcha ma'lumotlar to'g'rimi?",
        parse_mode="HTML",
        reply_markup=confirm_kb(),
    )
    return ORD_CONFIRM


async def ord_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "Yo'q" in text or "Bekor" in text:
        return await ord_cancel(update, context)

    user_id = update.effective_user.id
    ad_id = context.user_data.get("order_ad_id")
    order_type = context.user_data.get("order_type", "buy")
    card_photo = context.user_data.get("order_card_photo")

    # Ma'lumotlar bazasiga saqlash
    order_id = await db.create_order(
        buyer_id=user_id,
        ad_id=ad_id,
        order_type=order_type,
        card_photo=card_photo
    )

    user_db = await db.get_user(user_id)
    role = user_db.get("role", "user") if user_db else "user"

    await update.message.reply_text(
        f"🎉 <b>Buyurtma #{order_id} muvaffaqiyatli yuborildi!</b>\n\n"
        "⏳ Adminlarimiz chekni tekshirib, tez orada siz bilan bog'lanishadi.",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )

    # Adminlarni xabardor qilish
    ad_title = context.user_data.get("order_ad_title", "?")
    type_label = "Ijaraga olish" if order_type == "rent" else "Sotib olish"

    admin_text = (
        f"🔔 <b>YANGI BUYURTMA #{order_id}</b>\n\n"
        f"👤 Xaridor: {user_db.get('full_name', '?')}\n"
        f"📱 Tel: {user_db.get('phone', '?')}\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"📦 Mahsulot: {ad_title}\n"
        f"🏷 Turi: {type_label}"
    )

    for admin_id in ADMIN_IDS:
        try:
            # Rasm va boshqaruv tugmalarini yuborish
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=card_photo,
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=order_manage_inline(order_id)
            )
        except Exception as e:
            print(f"Admin {admin_id} xabar ololmadi: {e}")

    context.user_data.clear()
    return ConversationHandler.END


async def ord_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    role = user.get("role", "user") if user else "user"
    await update.message.reply_text("❌ Buyurtma berish bekor qilindi.", reply_markup=main_menu(role))
    context.user_data.clear()
    return ConversationHandler.END


# ─── FOYDALANUVCHI BUYURTMALARI RO'YXATI ─────────────────────────────────────

async def my_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    if not user or not user.get("phone"):
        await update.message.reply_text("⚠️ Avval ro'yxatdan o'ting!")
        return

    orders = await db.get_user_orders(user_id)
    if not orders:
        await update.message.reply_text("📭 Sizda hali buyurtmalar yo'q.")
        return

    status_emoji = {
        "pending": "⏳",
        "confirmed": "✅",
        "rejected": "❌",
        "completed": "🏁",
    }
    
    text = f"📋 <b>Sizning buyurtmalaringiz</b> ({len(orders)} ta):\n\n"
    
    for o in orders:
        emoji = status_emoji.get(o.get("status", "pending"), "•")
        type_str = "Ijara" if o.get("order_type") == "rent" else "Sotuv"
        
        # Sana xatosi (TypeError) oldini olish
        created_at = o.get('created_at')
        if isinstance(created_at, datetime):
            date_str = created_at.strftime('%d.%m.%Y')
        else:
            date_str = str(created_at)[:10] if created_at else "?"

        text += f"{emoji} <b>#{o['id']}</b> — {o.get('ad_title', '📦')} ({type_str}) | {date_str}\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ─── CONVERSATION HANDLER ─────────────────────────────────────────────────────

order_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(order_start_callback, pattern="^order_start_")],
    states={
        ORD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ord_type)],
        ORD_CARD: [
            MessageHandler(filters.PHOTO | filters.Document.IMAGE, ord_card),
            MessageHandler(filters.TEXT & ~filters.COMMAND, ord_card),
        ],
        ORD_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ord_confirm)],
    },
    fallbacks=[MessageHandler(filters.Regex("^❌ Bekor qilish$"), ord_cancel)],
    allow_reentry=True,
    per_message=False
)