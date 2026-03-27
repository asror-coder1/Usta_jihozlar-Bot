from telegram import Update
from telegram.ext import ContextTypes
import database as db
from keyboards import main_menu


async def usta_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    role = user.get("role", "user") if user else "user"

    await update.message.reply_text(
        "🔧 <b>Usta topish — UstaZone</b>\n\n"
        "UstaZone — O'zbekistondagi eng katta usta va mutaxassislar platformasi!\n\n"
        "🏠 Santexnik\n"
        "⚡ Elektrik\n"
        "🔨 Qurilish ustalari\n"
        "🖥 Kompyuter ta'mirlash\n"
        "🚗 Avto ta'mirlash\n"
        "va boshqa ko'plab xizmatlar...\n\n"
        "👇 Saytga o'ting va usta toping:",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )
    await update.message.reply_text(
        "🌐 <b>UstaZone veb-sayt:</b>\n"
        "https://ustazone.vercel.app/\n\n"
        "📱 <b>Telegram:</b> @ustazor_otp_bot",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )


async def about_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    role = user.get("role", "user") if user else "user"

    await update.message.reply_text(
        "ℹ️ <b>Bot haqida ma'lumot</b>\n\n"
        "🤖 Bu bot mahsulot va xizmatlarni sotish, ijaraga berish hamda "
        "buyurtma qabul qilish uchun mo'ljallangan.\n\n"
        "📦 <b>Imkoniyatlar:</b>\n"
        "• E'lon joylash (sotuv/ijara)\n"
        "• Buyurtma berish va kuzatish\n"
        "• Obuna orqali kengaytirilgan imkoniyatlar\n"
        "• Usta topish (UstaZone)\n"
        "• Admin boshqaruv paneli\n\n"
        "📞 <b>Aloqa:</b> Admin bilan bog'lanish uchun /admin yozing\n\n"
        "🙏 <i>Biz siz bilan har doim haq tanlamiz!</i>",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )
