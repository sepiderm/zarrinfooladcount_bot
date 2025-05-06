import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import os
from flask import Flask, request

# پیکربندی لاگ‌گیری
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# مراحل مکالمه
SELECT_TYPE, GET_DIMENSIONS, GET_PRICE = range(3)

# ذخیره اطلاعات کاربران
user_data = {}

# توکن بات
TOKEN = "8199021009:AAFKbVrDwfiI-qpMn2bGqFJVEsL8AQdP_3Q"

# هندلر شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ورق", callback_data='ورق')],
        [InlineKeyboardButton("میلگرد", callback_data='میلگرد')],
        [InlineKeyboardButton("نبشی", callback_data='نبشی')],
        [InlineKeyboardButton("ناودانی", callback_data='ناودانی')],
        [InlineKeyboardButton("تیرآهن", callback_data='تیرآهن')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("نوع آهن‌آلات را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_TYPE

async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id] = {'type': query.data}
    await query.edit_message_text(f"شما '{query.data}' را انتخاب کردید. لطفاً مشخصات را به این صورت وارد کنید:\nطول، عرض، ضخامت (متر)\nمثال: 2 1 0.005")
    return GET_DIMENSIONS

async def get_dimensions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        dimensions = list(map(float, update.message.text.strip().split()))
        if len(dimensions) != 3:
            raise ValueError
        user_data[user_id]['dimensions'] = dimensions
        length, width, thickness = dimensions
        volume = length * width * thickness
        density = 7850
        weight = volume * density
        user_data[user_id]['weight'] = weight
        await update.message.reply_text(f"✅ وزن: {weight:.2f} کیلوگرم\n\n📞 برای دریافت قیمت تماس بگیرید: 09123456789\n\nسپس قیمت هر کیلو را وارد کنید (تومان):")
        return GET_PRICE
    except ValueError:
        await update.message.reply_text("❌ ورودی نامعتبر. لطفاً دوباره وارد کنید:")
        return GET_DIMENSIONS

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        price_per_kg = float(update.message.text.strip())
        weight = user_data[user_id]['weight']
        total_price = weight * price_per_kg
        await update.message.reply_text(f"💰 قیمت کل: {total_price:,.0f} تومان")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ عدد وارد شده نامعتبر است. دوباره وارد کنید:")
        return GET_PRICE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔ عملیات لغو شد.")
    return ConversationHandler.END

# راه‌اندازی بات
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "OK"

if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_TYPE: [CallbackQueryHandler(select_type)],
            GET_DIMENSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dimensions)],
            GET_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    port = int(os.environ.get("PORT", 8080))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"https://your-app-name.up.railway.app/{TOKEN}"
    )
