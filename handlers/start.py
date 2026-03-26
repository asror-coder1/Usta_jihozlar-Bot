from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler

import database as db
from keyboards import main_menu, phone_kb, cancel_kb

PHONE, NAME = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = await db.get_user(user.id)

    if existing and existing.get("phone"):
        role = existing.get("role", "user")
        await update.message.reply_text(
            f"👋 Xush kelibsiz, <b>{existing['full_name']}</b>!\n\n"
            f"🤖 Botdan foydalanish uchun pastdagi menyudan tanlang:",
            parse_mode="HTML",
            reply_markup=main_menu(role),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Botdan foydalanish uchun avval ro'yxatdan o'ting.\n\n"
        "📱 Telefon raqamingizni yuboring:",
        parse_mode="HTML",
        reply_markup=phone_kb(),
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    else:
        phone = update.message.text.strip()
        if not phone.startswith("+"):
            phone = "+" + phone

    context.user_data["phone"] = phone
    await update.message.reply_text(
        "✅ Telefon qabul qilindi!\n\n"
        "📝 Endi to'liq ismingizni kiriting (F.I.Sh):",
        reply_markup=cancel_kb(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if name == "❌ Bekor qilish":
        return await cancel(update, context)

    phone = context.user_data.get("phone", "")
    user = update.effective_user

    await db.create_user(user.id, full_name=name, phone=phone)
    await db.update_user(user.id, full_name=name, phone=phone)

    existing = await db.get_user(user.id)
    role = existing.get("role", "user") if existing else "user"

    await update.message.reply_text(
        f"🎉 <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n\n"
        f"Pastdagi menyudan kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = await db.get_user(user.id)
    role = existing.get("role", "user") if existing else "user"
    await update.message.reply_text(
        "❌ Bekor qilindi.",
        reply_markup=main_menu(role),
    )
    return ConversationHandler.END


registration_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PHONE: [
            MessageHandler(filters.CONTACT, get_phone),
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
        ],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
    },
    fallbacks=[MessageHandler(filters.Regex("^❌ Bekor qilish$"), cancel)],
    allow_reentry=True,
)
