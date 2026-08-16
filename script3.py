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
