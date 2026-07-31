from steam_id import get_steam_id
import asyncio
from parser import get_player
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter, CommandObject
import os
from dotenv import load_dotenv
import logging
from formatters import format_player

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY = os.getenv("PROXY_URL")
router = Router()
logging.basicConfig(level=logging.DEBUG)

USER_ACCOUNTS = {
    "1": {"nick": "Нет аккаунта", "id": int},
    "2": {"nick": "Нет аккаунта", "id": int},
    "3": {"nick": "Нет аккаунта", "id": int}
}

class Form(StatesGroup):
    get_data = State()
    choose_topic = State()
    research_steam = State()
    waiting_nikname = State()
    waiting_steam = State()

topic_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📊 Последние матчи", callback_data="topic_matches")],
        [InlineKeyboardButton(text="🏆 Ранг", callback_data="topic_rank")],
        [InlineKeyboardButton(text="📈 Винрейт", callback_data="topic_winrate")],
        [InlineKeyboardButton(text="⏳ Недавно сыгранные герои", callback_data="topic_heroes")],
        [InlineKeyboardButton(text="🔍 Найти новый аккаунт", callback_data="topic_research")]
    ])

private_account_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📈 Винрейт", callback_data="topic_winrate")],
        [InlineKeyboardButton(text="🔍 Найти новый аккаунт", callback_data="topic_research")]
    ])

def get_accounts_keyboard() -> ReplyKeyboardMarkup:
    btn1_text = f"🎮 Аккаунт 1: {USER_ACCOUNTS["1"]["nick"]}"
    btn2_text = f"🎮 Аккаунт 2: {USER_ACCOUNTS["2"]["nick"]}"
    btn3_text = f"🎮 Аккаунт 3: {USER_ACCOUNTS["3"]["nick"]}"
    return ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=btn1_text),
        KeyboardButton(text=btn2_text)],
        [KeyboardButton(text=btn3_text)]],
    resize_keyboard=True,
    one_time_keyboard=False,
    is_persistent=True
    )
@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.update_data(player=None, data_dict=None)
    await msg.answer("Привет, Используй команду `/add 1`, `/add 2` или `/add 3`, чтобы привязать аккаунт.", 
        reply_markup=get_accounts_keyboard(),
        parse_mode="Markdown")
@router.message(Command("add"))
async def add_account(msg: Message, command: CommandObject, state: FSMContext):
    await state.update_data(player=None, data_dict=None)
    if not command.args or command.args not in ["1", "2", "3"]:
        await msg.answer("Ошибка! Пишите команду правильно, например: `/add 1`", parse_mode="Markdown")
        return
    
    button_num = command.args
    await state.update_data(chosen_button=button_num)
    await state.set_state(Form.waiting_steam)
    await msg.answer(f"Вы добавляете аккаунт на кнопку №{button_num}.\nПришлите ссылку или никнейм Steam профиля:")

@router.message(StateFilter(Form.waiting_steam))
async def get_link(msg: Message, state: FSMContext):
    try:
        steam = msg.text
        account_id = await get_steam_id(steam)
        await state.update_data(account_id=account_id)
        await state.set_state(Form.waiting_nikname)
        await msg.answer("Напишите никнейм, под которым у вас будет сохранен данный аккаунт на кнопке:")
    except Exception:
        logging.exception("SteamID error")
        await state.set_state(Form.waiting_steam)
        await msg.answer("Не нашёл профиль. Проверь ссылку или никнейм и попробуй ещё раз.")
        return

@router.message(StateFilter(Form.waiting_nikname))
async def get_nikname(msg: Message, state: FSMContext):
    nick = msg.text
    user_data = await state.get_data()
    button_num = user_data['chosen_button']
    account_id = user_data['account_id']
    USER_ACCOUNTS[button_num] = {
        "nick": nick,
        "id": account_id
    }
    await state.clear()
    await state.update_data(account_id=account_id)
    await msg.answer(
        f"Успешно! Аккаунт на кнопке {button_num} обновлен.\nНик: {nick}",
        reply_markup=get_accounts_keyboard()
    )
@router.message(F.text.startswith("🎮 Аккаунт"))
async def click_keyboard(msg: Message, state: FSMContext):
    await state.update_data(player=None, data_dict=None)
    num = msg.text.split("Аккаунт ")[1].split(":")[0]
    data = None

    if msg.text == f"🎮 Аккаунт {num}: Нет аккаунта":
        await msg.answer("Этот слот пуст. Используйте команду `/add [номер]`, чтобы добавить аккаунт.", parse_mode="Markdown")
        return
    else:
        chosen_acc = num
    # user_data = await state.get_data()
    account_id = USER_ACCOUNTS[num].get('id')
    if chosen_acc:
        try:
            await state.set_state(Form.choose_topic)
            data = await get_player(account_id)
            await state.update_data(player=data['data']['player'], data_dict=data)
            errors = data.get('errors')
            if errors and isinstance(errors, list):
                error_message = errors[0].get('message', '')
                if "anonymous" in error_message:
                    text =  "Это приватный аккаунт"
                    try:
                        await msg.answer(text, parse_mode="HTML", reply_markup=private_account_button)
                    except TelegramBadRequest as e:
                        if "message is not modified" not in str(e):
                            raise
            else:
                await msg.answer("Нашел профиль, что посмотреть?", reply_markup=topic_button)
        except Exception:
            logging.exception("Stratz error")
            await msg.answer(
                "⚠️ Ошибка при запросе к Stratz. Повторите попытку или попробуйте позже.", 
                reply_markup=topic_button
            )
            return
@router.message(StateFilter(Form.research_steam))
async def research_steam(msg: Message, state: FSMContext):
    await state.update_data(player=None, data_dict=None)
    text = msg.text
    try:
        account_id = await get_steam_id(text)
        
        # await state.update_data(account_id=account_id)
        await state.set_state(Form.choose_topic)
        try:
            data = await get_player(account_id)
            await state.update_data(data_dict=data, account_id=account_id)
            errors = data.get('errors')
            if errors and isinstance(errors, list):
                error_message = errors[0].get('message', '')
                if "anonymous" in error_message:
                    text =  "Это приватный аккаунт"
                    try:
                        await msg.answer(text, parse_mode="HTML", reply_markup=private_account_button) 
                    except TelegramBadRequest as e:
                        if "message is not modified" not in str(e):
                            raise
            else:
                await msg.answer("Нашел профиль, что посмотреть?", reply_markup=topic_button)
        except Exception:
            logging.exception("Stratz error")
            await msg.answer(
                "⚠️ Ошибка при запросе к Stratz. Повторите попытку или попробуйте позже.", 
                reply_markup=topic_button
            )
            return
    except Exception:
        logging.exception("SteamID error")
        await msg.answer("Не нашёл профиль. Проверь имя и попробуй ещё раз.")
        return
@router.callback_query(StateFilter(Form.choose_topic), F.data.startswith("topic_"))
async def on_topic(cb: CallbackQuery, state: FSMContext):
    topic = cb.data.split("_")[1]
    state_data = await state.get_data()
    data = state_data.get('data_dict')
    try:
        account_id = state_data.get('account_id')
    except Exception:
        account_id = data.get('steamAccountId')
    player = state_data.get('player')
    await cb.answer()
    if topic == "research":
        await state.clear()
        await state.set_state(Form.research_steam)
        await cb.message.edit_text("Пришли новый стим аккаунт")
        return
    try:
        if not player:
            data = await get_player(account_id)
            player = data['data']['player']
            await state.update_data(player=player, data_dict=data)
    except Exception:
        logging.exception("Stratz error")
        await cb.message.edit_text(
            "⚠️ Ошибка при запросе к Stratz. Повторите попытку или попробуйте позже.", 
            reply_markup=topic_button
        )
        return
    errors = data.get('errors')
    if errors and isinstance(errors, list):
        error_message = errors[0].get('message', '')
        if "anonymous" in error_message:
            text = format_player(player, topic)
            try:
                await cb.message.edit_text(text, parse_mode="HTML", reply_markup=private_account_button)
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
    else:
        await state.update_data(player=player) 
        text = format_player(player, topic)
        if not text:
            text = "❌ Нет данных"
        try:
            await cb.message.edit_text(text, parse_mode="HTML", reply_markup=topic_button)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
    
async def main():
    session = AiohttpSession(proxy=PROXY)
    bot = Bot(BOT_TOKEN, session=session)
    dp = Dispatcher()
    dp.include_router(router)
    try:
        await dp.start_polling(bot)
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())