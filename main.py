import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

BOT_TOKEN = "8935945535:AAGNrZhDJl290DgDIfOZVq6lS3KZXrZjfvQ"
ADMIN_ID = 1722349114
PRIVAT_LINK = "https://t.me/+v73ppsyz22w1ZGIy"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class FeedbackState(StatesGroup):
    waiting_for_message = State()

def get_main_menu():
    kb = [
        [KeyboardButton(text="💬 Поддержка и предложения")],
        [KeyboardButton(text="💎 Приватный канал")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(F.text == "/start")
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в neurovibeBOT! ⚡️\n\n"
        f"Здесь ты можешь получить доступ к нашему закрытому комьюнити или связаться с администрацией.\n\n"
        f"Что тут можно сделать?\n"
        f"💎 Приватный канал — забрать актуальную ссылку на вход в приватку.\n"
        f"💬 Поддержка и предложения — задать вопрос, сообщить о проблеме или поделиться своей крутой идеей. Пиши, админ читает абсолютно всё!\n\n"
        f"Выбирай нужный раздел в меню ниже 👇",
        reply_markup=get_main_menu()
    )


@dp.message(F.text == "💎 Приватный канал")
async def open_private(message: Message):
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вступить в приватку 🚀", url=PRIVAT_LINK)]
    ])
    await message.answer(
        "Доступ в наш закрытый приватный канал открыт по кнопке ниже:",
        reply_markup=inline_kb
    )

@dp.message(F.text == "💬 Поддержка и предложения")
async def start_feedback(message: Message, state: FSMContext):
    await state.set_state(FeedbackState.waiting_for_message)
    await message.answer(
        "Напиши своё обращение, вопрос или предложение в одном сообщении "
        "(можно прикрепить фото), и я сразу передам его админу! ✍️\n\n"
        "Для отмены просто напиши слово: отмена"
    )
    @dp.message(FeedbackState.waiting_for_message)
async def forward_to_admin(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu())
        return

    # Формируем красивую карточку. Обязательно оставляем ID юзера в первой строчке!
    user_info = (
        f"📩 **Новое обращение!**\n"
        f"👤 От: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"🆔 ID: `{message.from_user.id}`\n"
        f"✍️ Текст: {message.text if message.text else '[Вложение]'}\n"
    )
    
    # 1. Отправляем админу в личку
    await bot.send_message(chat_id=ADMIN_ID, text=user_info, parse_mode="Markdown")
    if not message.text: # Если это фото или файл — пересылаем следом
        await message.forward(chat_id=ADMIN_ID)
    
    # 2. Дублируем в группу (если GROUP_ID настроен)
    try:
        await bot.send_message(chat_id=GROUP_ID, text=user_info, parse_mode="Markdown")
        if not message.text:
            await message.forward(chat_id=GROUP_ID)
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")
    
    await state.clear()
    await message.answer("Спасибо! Твое сообщение успешно отправлено администратору. Ожидай ответа.", reply_markup=get_main_menu())

# --- НАЧАЛО НОВОГО КОДА ДЛЯ ОТВЕТА ПОЛЬЗОВАТЕЛЮ ---

@dp.message(F.reply_to_message)
async def reply_to_user(message: Message):
    # Проверяем, что отвечает именно админ (в личке или в нашей группе)
    is_admin_cl = message.chat.id == ADMIN_ID
    is_admin_gr = 'GROUP_ID' in globals() and message.chat.id == GROUP_ID
    
    if not (is_admin_cl or is_admin_gr):
        return

    # Берем сообщение, на которое админ нажал "Ответить"
    reply = message.reply_to_message
    if not reply.text:
        return

    # Вытаскиваем ID пользователя из текста карточки
    try:
        lines = reply.text.split("\n")
        user_id_line = [line for line in lines if "ID:" in line or "🆔 ID:" in line][0]
        # Очищаем строчку от букв и знаков, оставляя только цифры ID
        user_id = int(''.join(filter(str.isdigit, user_id_line)))
    except Exception:
        await message.answer("❌ Не удалось найти ID пользователя в этом сообщении. Ответить не получится.")
        return

    # Пересылаем ответ админа пользователю
    try:
        if message.text:
            await bot.send_message(chat_id=user_id, text=f"💬 **Ответ от администрации:**\n\n{message.text}", parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=user_id, text=f"💬 **Ответ от администрации (вложение):**\n", parse_mode="Markdown")
            await message.copy_to(chat_id=user_id)
            
        await message.answer("✅ Ответ успешно доставлен пользователю!")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение. Возможно, пользователь заблокировал бота. Ошибка: {e}")

# --- КОНЕЦ НОВОГО КОДА ---

# Хак для обхода спящего режима Render (мини веб-сервер)
async def handle(request):
    return web.Response(text="Бот работает!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

async def main():
    await start_webserver()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

"Спасибо! Твое сообщение успешно отправлено администратору. Ожидай ответа.", reply_markup=get_main_menu())

# Хак для обхода спящего режима Render (мини веб-сервер)
async def handle(request):
    return web.Response(text="Бот работает!")


# Хак для обхода спящего режима Render (мини веб-сервер)
async def handle(request):
    return web.Response(text="Бот работает!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

async def main():
    await start_webserver()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
