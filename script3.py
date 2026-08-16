import asyncio
import logging
import os
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from flask import Flask

# 1. Запуск веб-сервера для Render (щоб бот працював 24/7)
app = Flask('')


@app.route('/')
def home():
  return 'Bot is alive!'


def run_flask():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


# 2. Отримання токена зі змінних оточення
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# 3. Стартове повідомлення та кнопка запиту контакту
@dp.message(Command('start'))
async def start_cmd(message: types.Message):
  kb = ReplyKeyboardMarkup(
      keyboard=[
          [
              KeyboardButton(
                  text='📱 Надіслати номер телефону', request_contact=True
              )
          ]
      ],
      resize_keyboard=True,
  )
  await message.answer(
      'Раді бачити вас у боті! Надішліть номер телефону для перевірки:',
      reply_markup=kb,
  )


# 4. Обробка отриманого контакту та відкриття головного меню
@dp.message(F.contact)
async def contact_handler(message: types.Message):
  name = message.contact.first_name

  menu_kb = ReplyKeyboardMarkup(
      keyboard=[
          [
              KeyboardButton(text='🏢 Особистий кабінет'),
              KeyboardButton(text='💰 Заробити'),
          ],
          [KeyboardButton(text='📊 Статистика')],
      ],
      resize_keyboard=True,
  )

  await message.answer(f'👋 Привіт, {name}!', reply_markup=menu_kb)


# 5. Обробка натискань на кнопки меню
@dp.message(F.text == '🏢 Особистий кабінет')
async def profile_handler(message: types.Message):
  await message.answer('Ваш особистий кабінет:\nСтатус: Активний ✅')


@dp.message(F.text == '💰 Заробити')
async def earn_handler(message: types.Message):
  await message.answer(
      "Розділ 'Заробити':\nВаше реферальне посилання з'явиться тут."
  )


@dp.message(F.text == '📊 Статистика')
async def stats_handler(message: types.Message):
  await message.answer('Загальна статистика:\nЗапрошено друзів: 0\nЗароблено: 0 грн')


# 6. Запуск сервера та бота
async def main():
  # Запускаємо Flask у окремому фоновому потоці
  t = Thread(target=run_flask)
  t.daemon = True
  t.start()

  logging.basicConfig(level=logging.INFO)
  # Очищаємо старі вебхуки та запускаємо polling
  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if name == 'main':
  asyncio.run(main())
