import asyncio
import logging
import os
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from flask import Flask

# 1. Створення Flask-сервера
app = Flask('')


@app.route('/')
def home():
  return 'Bot is alive!'


def run_flask():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


# 2. Запуск Flask у фоновому потоці ОДРАЗУ
t = Thread(target=run_flask)
t.daemon = True
t.start()

# 3. Налаштування бота
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# 4. Обробники
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


# 5. Головна асинхронна функція
async def main():
  logging.basicConfig(level=logging.INFO)
  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == '__main__':
  asyncio.run(main())
