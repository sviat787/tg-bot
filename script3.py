import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# === НАЛАШТУВАННЯ ===
BOT_TOKEN = "ТВІЙ_ТОКЕН_БОТА"  # Вставити токен від @BotFather
PRIMARY_ADMIN_ID = 5406292948  # Твій Telegram ID (Головний адмін)
PROOF_CHANNEL_ID = -1001234567890  # ID твого каналу

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

BALANCES_FILE = "balances.json"
ADMINS_FILE = "admins.json"


# === УПРАВЛІННЯ СПИСКОМ АДМІНІВ ===
def load_admins():
    if not os.path.exists(ADMINS_FILE):
        return [PRIMARY_ADMIN_ID]
    with open(ADMINS_FILE, "r", encoding="utf-8") as f:
        admins = json.load(f)
        if PRIMARY_ADMIN_ID not in admins:
            admins.append(PRIMARY_ADMIN_ID)
        return admins


def save_admins(admins):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, ensure_ascii=False, indent=4)


def is_admin(user_id: int) -> bool:
    return user_id in load_admins()


# === РОБОТА З БАЛАНСАМИ ===
def load_balances():
    if not os.path.exists(BALANCES_FILE):
        return {}
    with open(BALANCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_balances(data):
    with open(BALANCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_user_balance(user_id: int) -> float:
    balances = load_balances()
    return balances.get(str(user_id), 0.0)


def update_user_balance(user_id: int, amount: float):
    balances = load_balances()
    str_id = str(user_id)
    current = balances.get(str_id, 0.0)
    balances[str_id] = round(current + amount, 2)
    save_balances(balances)
    return balances[str_id]


class PayoutState(StatesGroup):
    wait_amount = State()
    wait_card = State()


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="💸 Вивести кошти")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📣 Канал виплат")]
        ],
        resize_keyboard=True
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привіт! Обери необхідний розділ у меню нижче:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "💰 Баланс")
async def show_user_balance(message: Message):
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"💳 Ваш поточний баланс: <b>{balance:.2f} грн</b>", parse_mode="HTML")


# === КЕРУВАННЯ АДМІНІСТРАТОРАМИ ===

# Назначити адміна: /addadmin 123456789
@router.message(Command("addadmin"))
async def cmd_add_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    try:
        _, new_admin_id = message.text.split()
        new_admin_id = int(new_admin_id)

        admins = load_admins()
        if new_admin_id in admins:
            await message.answer("⚠️ Цей користувач вже є адміністратором.")
            return

        admins.append(new_admin_id)
        save_admins(admins)
        await message.answer(f"✅ Користувача <code>{new_admin_id}</code> успішно призначено адміністратором!", parse_mode="HTML")
        
        try:
            await bot.send_message(chat_id=new_admin_id, text="🎉 Вас призначено адміністратором бота!")
        except Exception:
            pass

    except ValueError:
        await message.answer("❌ Формат команди: <code>/addadmin ID_користувача</code>", parse_mode="HTML")


# Видалити адміна: /deladmin 123456789
@router.message(Command("deladmin"))
async def cmd_del_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    try:
        if admin_to_remove == PRIMARY_ADMIN_ID:
            await message.answer("❌ Неможливо видалити головного адміністратора!")
            return

        admins = load_admins()
        if admin_to_remove not in admins:
            await message.answer("⚠️ Цього користувача немає у списку адмінів.")
            return

        admins.remove(admin_to_remove)
        save_admins(admins)
        await message.answer(f"✅ Користувача <code>{admin_to_remove}</code> вилучено з адміністраторів.", parse_mode="HTML")

    except ValueError:
        await message.answer("❌ Формат команди: <code>/deladmin ID_користувача</code>", parse_mode="HTML")


# Переглянути список адмінів: /admins
@router.message(Command("admins"))
async def cmd_list_admins(message: Message):
    if not is_admin(message.from_user.id):
        return

    admins = load_admins()
    text = "👑 <b>Список адміністраторів:</b>\n\n"
    for admin_id in admins:
        text += f"• <code>{admin_id}</code>\n"
    await message.answer(text, parse_mode="HTML")


# === КЕРУВАННЯ БАЛАНСОМ ===

@router.message(Command("addbalance"))
async def cmd_add_balance(message: Message):
    if not is_admin(message.from_user.id):
        return

    try:
        _, target_id, amount = message.text.split()
        target_id = int(target_id)
        amount = float(amount)

        new_balance = update_user_balance(target_id, amount)
        await message.answer(f"✅ Додано {amount} грн користувачу <code>{target_id}</code>.\nНовий баланс: <b>{new_balance} грн</b>", parse_mode="HTML")
        
        try:
            await bot.send_message(chat_id=target_id, text=f"💰 Ваш баланс поповнено на <b>{amount} грн</b>!", parse_mode="HTML")
        except Exception:
            pass
    except ValueError:
        await message.answer("❌ Формат команди: <code>/addbalance ID_користувача сума</code>", parse_mode="HTML")


@router.message(Command("subbalance"))
async def cmd_sub_balance(message: Message):
    if not is_admin(message.from_user.id):
        return

    try:
        _, target_id, amount = message.text.split()
        target_id = int(target_id)
        amount = float(amount)

        new_balance = update_user_balance(target_id, -amount)
        await message.answer(f"✅ Знято {amount} грн у користувача <code>{target_id}</code>.\nНовий баланс: <b>{new_balance} грн</b>", parse_mode="HTML")
        
        try:
            await bot.send_message(chat_id=target_id, text=f"💸 З вашого балансу списано <b>{amount} грн</b>.", parse_mode="HTML")
        except Exception:
            pass
    except ValueError:
        await message.answer("❌ Формат команди: <code>/subbalance ID_користувача сума</code>", parse_mode="HTML")


# === СТАТИСТИКА ТА ВИПЛАТИ ===

@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    stats_text = (
        "📈 <b>СТАТИСТИКА ПРОЄКТУ</b>\n"
        "───────────────\n\n"
        "📊 <b>Активність:</b>\n"
        " ┣ 👥 Учасників: <b>5</b>\n"
        " ┣ ⚡ Активні за тиждень: <b>5</b>\n"
        " ┗ 🎯 Рефералів: <b>0</b>\n\n"
        "💳 <b>Фінанси:</b>\n"
        " ┣ 💰 Баланс користувачів: <b>3 990 грн</b>\n"
        " ┣ 💸 Виплачено: <b>250 грн</b>\n"
        " ┗ ⏳ В обробці: <b>1 заявка</b>\n\n"
        "───────────────\n"
        "👑 <b>Адміністрація:</b> @sviat787"
    )
    await message.answer(stats_text, parse_mode="HTML")


@router.message(F.text == "📣 Канал виплат")
async def show_channel_info(message: Message):
    await message.answer("Переглянути всі виплати та докази можна у нашому каналі!")


@router.message(F.text == "💸 Вивести кошти")
@router.message(Command("payout"))
async def start_payout(message: Message, state: FSMContext):
    user_balance = get_user_balance(message.from_user.id)
    if user_balance <= 0:
        await message.answer("❌ У вас недостатньо коштів на балансі для виведення.")
        return
        await state.set_state(PayoutState.wait_amount)
        await message.answer(f"Ваш баланс: <b>{user_balance} грн</b>\nВведіть суму для виплати:", parse_mode="HTML")
@router.message(PayoutState.wait_amount)
async def process_amount(message: Message , state :FSMContext):
    try:
        amount = float(message.text)
        user_balance = get_user_balance(message.from_user.id)

        if amount <= 0 or amount > user_balance:
            await message.answer("❌ Некоректна сума або перевищує ваш баланс. Спробуйте ще раз:")
            return

        await state.update_data(amount=amount)
        await state.set_state(PayoutState.wait_card)
        await message.answer("Введіть номер картки та ПІБ отримувача:")
    except ValueError:
        await message.answer("Будь ласка, введіть число (наприклад, 100 або 250.50):")


@router.message(PayoutState.wait_card)
async def process_card(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data['amount']
    card_info = message.text
    user = message.from_user

    update_user_balance(user.id, -amount)

    await state.clear()
    await message.answer("✅ Заявку прийнято! Вона відправлена адміністратору. Очікуйте переказу.")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Виплачено", callback_data=f"done_{user.id}_{amount}"),
            InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{user.id}_{amount}")
        ]
    ])
    
    admin_text = (
        f"📥 <b>Нова заявка на виплату!</b>\n\n"
        f"👤 Користувач: {user.full_name} (@{user.username})\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"💵 Сума: <b>{amount} грн</b>\n"
        f"💳 Картка: <code>{card_info}</code>"
    )
    
    for admin_id in load_admins():
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass


@router.callback_query(F.data.startswith("done_"))
async def confirm_payout(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    _, user_id, amount = call.data.split("_")

    try:
        await bot.send_message(
            chat_id=int(user_id), 
            text=f"🎉 <b>Виплату виконано!</b>\nНа вашу картку перераховано {amount} грн.", 
            parse_mode="HTML"
        )
    except Exception:
        pass

    channel_text = (
        f"💸 <b>Успішна виплата!</b>\n\n"
        f"🔹 Сума: <b>{amount} грн</b>\n"
        f"🔹 Статус: Виконано ✅\n"
        f"🔹 Дякуємо за роботу!"
    )
    try:
        await bot.send_message(chat_id=PROOF_CHANNEL_ID, text=channel_text, parse_mode="HTML")
    except Exception as e:
        await call.answer(f"Помилка відправки в канал: {e}", show_alert=True)

    await call.message.edit_text(f"{call.message.text}\n\n✅ <b>ВИПЛАЧЕНО (Обробив @{call.from_user.username})</b>", parse_mode="HTML")


@router.callback_query(F.data.startswith("reject_"))
async def reject_payout(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    _, user_id, amount = call.data.split("_")
    
    update_user_balance(int(user_id), float(amount))

    try:
        await bot.send_message(
            chat_id=int(user_id), 
            text=f"❌ Вашу заявку на виплату {amount} грн відхилено. Кошти повернуто на ваш баланс.", 
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.message.edit_text(f"{call.message.text}\n\n❌ <b>ВІДХИЛЕНО (Обробив @{call.from_user.username})</b>", parse_mode="HTML")


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
