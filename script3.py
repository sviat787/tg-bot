import asyncio
import logging
import os
import sqlite3
from threading import Thread

from aiogram import Bot, Dispatcher, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from flask import Flask

# ================= 1. НАЛАШТУВАННЯ ТА КАНАЛИ =================
# Додайте сюди ваші канали
CHANNELS = [
    {"id": "@oiuysn", "link": "https://t.me/oiuysn", "name": "Канал 1"},
    {"id": "@sellerwear", "link": "https://t.me/sellerwear", "name": "Канал 2"},
]

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            balance REAL DEFAULT 0.0,
            referrals_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= 2. FLASK СЕРВЕР (для UptimeRobot) =================
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

t = Thread(target=run_flask)
t.daemon = True
t.start()

# ================= 3. ІНІЦІАЛІЗАЦИЯ БОТА =================
API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================= 4. КЛАВІАТУРИ =================
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏦 Особистий кабінет"),
            KeyboardButton(text="💸 Заробити"),
        ],
        [
            KeyboardButton(text="💰 Завдання"),
            KeyboardButton(text="📝 Замовити рекламу"),
        ],
        [KeyboardButton(text="📊 Статистика")],
    ],
    resize_keyboard=True,
)

def get_sub_keyboard():
    buttons = []
    for ch in CHANNELS:
        buttons.append(
            [InlineKeyboardButton(text=f"📢 Підписатися на {ch['name']}", url=ch["link"])]
        )
    buttons.append(
        [InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ================= 5. ВСПОМІЖНІ ФУНКЦІЇ =================
async def is_subscribed_all(user_id: int) -> bool:
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status not in ["creator", "administrator", "member"]:
                return False
        except TelegramBadRequest:
            return False
    return True

# ================= 6. ОБРОБНИКИ =================
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    referrer_id = command.args

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        ref_id = None
        if referrer_id and referrer_id.isdigit() and int(referrer_id) != user_id:
            ref_id = int(referrer_id)
            cursor.execute("UPDATE users SET balance = balance + 5.0, referrals_count = referrals_count + 1 WHERE user_id = ?", (ref_id,))
            try:
                await bot.send_message(chat_id=ref_id, text="🎉 За вашим посиланням зареєструвався новий користувач! Вам нараховано 5 ₴.")
            except Exception: pass
        cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, ref_id))
        conn.commit()
    conn.close()

    if await is_subscribed_all(user_id):
        await message.answer(f"👋 Привіт, {message.from_user.first_name}!", reply_markup=main_keyboard)
    else:
        await message.answer("⚠️ Для використання бота необхідно підписатися на наші канали!", reply_markup=get_sub_keyboard())
        @dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: types.CallbackQuery):
    if await is_subscribed_all(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("✅ Дякуємо за підписку!", reply_markup=main_keyboard)
    else:
        await callback.answer("❌ Ви підписалися не на всі канали!", show_alert=True)

@dp.message(F.text == "🏦 Особистий кабінет")
async def profile_handler(message: types.Message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, referrals_count FROM users WHERE user_id = ?", (message.from_user.id,))
    data = cursor.fetchone()
    conn.close()
    balance = data[0] if data else 0.0
    refs = data[1] if data else 0
    await message.answer(f"👤 Ваш особистий кабінет:\n\n💰 Баланс: {balance} ₴\n👥 Запрошено друзів: {refs}", parse_mode="Markdown")

@dp.message(F.text == "💸 Заробити")
async def earn_handler(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(f"💸 | За кожного реферала ви будете отримувати 5.0 ₴\n\nℹ️ Ваше посилання:\n{ref_link}", parse_mode="Markdown")

@dp.message(F.text == "📝 Замовити рекламу")
async def adv_handler(message: types.Message):
    await message.answer("Щоб замовити рекламу, пишіть до @sviat787")

@dp.message(F.text == "💰 Завдання")
async def tasks_handler(message: types.Message):
    await message.answer("Наразі доступних завдань немає.")

@dp.message(F.text == "📊 Статистика")
async def stats_handler(message: types.Message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(balance) FROM users")
    data = cursor.fetchone()
    conn.close()
    await message.answer(f"📊 Всього користувачів: {data[0] if data else 0}", parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
