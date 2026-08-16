import os
from threading import Thread
from flask import Flask

app = Flask('')


@app.route('/')
def home():
  return 'Bot is alive!'


def run():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


Thread(target=run).start()
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import os
API_TOKEN = os.getnev("BOT TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. Стартове повідомлення та кнопка запиту контакту
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Надіслати номер телефону", request_contact=True)]
        ],
        resize_keyboard=True
    )
    await message.answer("Раді бачити вас у боті! Надішліть номер телефону для перевірки:", reply_markup=kb)

# 2. Обробка отриманого контакту та відкриття головного меню
@dp.message(F.contact)
async def contact_handler(message: types.Message):
    name = message.contact.first_name

    # Головне меню з кнопками
    menu_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Особистий кабінет"), KeyboardButton(text="💰 Заробити")],
            [KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True
    )

    await message.answer(f"👋 Привіт, {name}!", reply_markup=menu_kb)

# 3. Обробка натискань на кнопки меню
@dp.message(F.text == "🏢 Особистий кабінет")
async def profile_handler(message: types.Message):
    await message.answer("Ваш особистий кабінет:\nСтатус: Активний ✅")

@dp.message(F.text == "💰 Заробити")
async def earn_handler(message: types.Message):
    await message.answer("Розділ 'Заробити':\nВаше реферальне посилання з'явиться тут.")

@dp.message(F.text == "📊 Статистика")
async def stats_handler(message: types.Message):
    await message.answer("Загальна статистика:\nЗапрошено друзів: 0\nЗароблено: 0 грн")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
