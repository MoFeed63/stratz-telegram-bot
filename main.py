import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from database import close_db, get_user_slots, init_db, update_user_slot
from dotenv import load_dotenv
from formatters import format_player
from parser import get_player
from steam_id import get_steam_id

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
async def get_accounts_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    user = await get_user_slots(user_id)
    btn1_text = f"🎮 Аккаунт 1: {user["slot_1"].get("nick")}"
    btn2_text = f"🎮 Аккаунт 2: {user["slot_2"]["nick"]}"
    btn3_text = f"🎮 Аккаунт 3: {user["slot_3"]["nick"]}"
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
    user_id = msg.from_user.id
    await msg.answer("Привет, Используй команду `/add 1`, `/add 2` или `/add 3`, чтобы привязать аккаунт.", 
        reply_markup=await get_accounts_keyboard(user_id),
        parse_mode="Markdown")
@router.message(Command("add"))
async def add_account(msg: Message, command: CommandObject, state: FSMContext):
    await state.update_data(player=None, data_dict=None)
    if not command.args or command.args not in ["1", "2", "3"]:
        await msg.answer("Ошибка! Пишите команду правильно, например: `/add 1`", parse_mode="Markdown")
        return

    user_id = msg.from_user.id
    slot_num = command.args
    # await update_user_slot(user_id=user_id, slot_num=button_num)
    await state.update_data(chosen_slot=slot_num)
    await state.set_state(Form.waiting_steam)
    await msg.answer(f"Вы добавляете аккаунт на кнопку №{slot_num}.\nПришлите ссылку или никнейм Steam профиля:")

@router.message(StateFilter(Form.waiting_steam))
async def get_link(msg: Message, state: FSMContext):
    try:
        steam = msg.text
        account_id = await get_steam_id(steam)
        await state.update_data(account_id=account_id)
        await state.set_state(Form.waiting_nikname)
        # await update_user_slot(account_id=account_id)
        await msg.answer("Напишите никнейм, под которым у вас будет сохранен данный аккаунт на кнопке:")
    except Exception:
        logging.exception("SteamID error")
        await state.set_state(Form.waiting_steam)
        await msg.answer("Не нашёл профиль. Проверь ссылку или никнейм и попробуй ещё раз.")
        return

@router.message(StateFilter(Form.waiting_nikname))
async def get_nikname(msg: Message, state: FSMContext):
    nick = msg.text
    user_id = msg.from_user.id
    # await update_user_slot(nick=nick)
    state_data = await state.get_data()
    account_id = state_data['account_id']
    # user_data = await get_user_slots(user_id)
    slot_num = state_data['chosen_slot']
    # account_id = user_data[f'slot_{button_num}']['id']
    await state.clear()
    await update_user_slot(user_id=user_id, slot_num=slot_num, account_id=account_id, nick=nick)
    await msg.answer(
        f"Успешно! Аккаунт на кнопке {slot_num} обновлен.\nНик: {nick}",
        reply_markup=await get_accounts_keyboard(user_id)
    )
@router.message(F.text.startswith("🎮 Аккаунт"))
async def click_keyboard(msg: Message, state: FSMContext):
    await state.update_data(player=None, data_dict=None)
    num = msg.text.split("Аккаунт ")[1].split(":")[0]
    data = None

    if msg.text == f"🎮 Аккаунт {num}: None":
        await msg.answer("Этот слот пуст. Используйте команду `/add [номер]`, чтобы добавить аккаунт.", parse_mode="Markdown")
        return
    else:
        chosen_acc = num
    # user_data = await state.get_data()
    user_slots = await get_user_slots(msg.from_user.id)
    account_id = user_slots[f"slot_{num}"]['id']
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
    await init_db()
    session = AiohttpSession(proxy=PROXY)
    bot = Bot(BOT_TOKEN, session=session)
    dp = Dispatcher()
    dp.include_router(router)
    try:
        await dp.start_polling(bot)
    finally:
        await session.close()
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())