from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import asyncio
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from config_reader import config
from TgUser import TgUser
from StateMachine import State
from dbServing import UsersTable, NotificationTable
from FeedbackState import FeedbackState
import UserNotification
from aiogram.types import InlineKeyboardButton, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()


async def load_user_from_db(tg_id):
    query = UsersTable.get_or_none(UsersTable.tg_id == tg_id)
    if query is not None:
        user = TgUser(
            tg_id=query.tg_id,
            name=query.name,
            surname=query.surname,
            username=query.username,
            confirm_code=query.confirm_code,
            is_attached=query.is_attached)
    else:
        user = query
    return user


class InnerCallbackQueryUniqueClientMiddleware(BaseMiddleware):
    def __init__(self):
        self.users = None

    async def __call__(self, handler, event: types.Message, data):
        await self.load(event.from_user.id)
        data["tg_user"] = self.users
        return await handler(event, data)

    async def load(self, tg_id):
        self.users = await load_user_from_db(tg_id)


@dp.message(Command("start"))
async def handler_start(message: types.Message, state: FSMContext, tg_user: Any):
    print(tg_user)
    if tg_user is None:
        UsersTable.create(tg_id=message.from_user.id, name=message.from_user.first_name,
                          surname=message.from_user.last_name, username=message.from_user.username)

        kb = [
            [types.KeyboardButton(text="Connect Account")],
            [types.KeyboardButton(text="Deactivate Account")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Choose action")
        await message.answer("Welcome! What would you like to do?", reply_markup=keyboard)
        await state.set_state(State.START)
    else:
        await message.answer("You're already registered")


@dp.message(StateFilter(None, State.START), F.text == "Connect Account")
async def handler_button_activate(message: types.Message, state: FSMContext, tg_user: TgUser):
    print(await state.get_state())
    if tg_user.is_attached():
        await message.answer("You're already registered or can't be registered now")

    elif tg_user is None:
        tg_user.activate()
        await message.answer("Enter the activation code:")
        await state.set_state(State.ON_VALIDATION)
    else:
        await state.set_state(State.WAIT_NOTIFICATION)
        await message.answer("You're registered.")


@dp.message(StateFilter(State.WAIT_NOTIFICATION), F.text == "Deactivate Account")
async def handler_button_deactivate(message: types.Message, state: FSMContext, tg_user):
    if tg_user:
        tg_user.deactivate()
        await message.answer("Enter the deactivation code:")
        await state.set_state(State.GET_CODE)


@dp.message(StateFilter(State.ON_VALIDATION, State.GET_CODE), lambda message: len(message.text) == 8)
async def code_handler(message: types.Message, state: FSMContext, tg_user):
    if tg_user:
        current_state = await state.get_state()
        if current_state == State.ON_VALIDATION:
            if tg_user.confirm_activate(message.text):
                await message.answer("Activation code accepted. Account activated.")
                await state.set_state(State.WAIT_NOTIFICATION)
            else:
                await message.answer("Invalid activation code.")
                await state.set_state(State.START)
        elif current_state == State.GET_CODE:
            if tg_user.confirm_deactivate(message.text):
                await message.answer("Deactivation code accepted. Account deactivated.")
                await state.set_state(State.START)
            else:
                await message.answer("Invalid deactivation code.")
                await state.set_state(State.WAIT_NOTIFICATION)
    else:
        await message.answer("You are not registered.")


@dp.callback_query(lambda callback_query: callback_query.data.startswith("read_"))
async def handle_read_button(callback_query: types.CallbackQuery):
    notification_id = callback_query.data.split("_")[1]
    NotificationTable.update(
        {NotificationTable.feedback: FeedbackState.CONFIRM}
    ).where(NotificationTable.id == notification_id).execute()

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "You have acknowledged the notification.")


async def send_notification_to_users(name, notification_text, level, is_inline):
    query = UsersTable.select(UsersTable.tg_id).where(UsersTable.is_attached == True).execute()
    print(query)
    for user in query:
        notification = NotificationTable.create(
            uid=user.tg_id,
            note_name=name,
            level=level
        )
        print(user.tg_id)
        if level == "critical" or is_inline:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="I've read", callback_data=f"read_{notification.id}"))
            await bot.send_message(user.tg_id, notification_text, reply_markup=builder.as_markup(),
                                   parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await bot.send_message(user.tg_id, notification_text, parse_mode=ParseMode.MARKDOWN_V2)


@dp.message(Command("gen"))
async def generate_notification(message: types.Message):
    notification_levels = ["info", "warning", "critical"]
    name = f"Notification_{random.randint(1, 1000)}"
    text = f"This is a {random.choice(['test', 'sample', 'example'])} notification with ID {random.randint(10000, 99999)}"
    level = random.choice(notification_levels)
    is_blur = random.choice([True, False])
    is_inline = random.choice([True, False])
    notification = UserNotification.UserNotification(name, text, level, type_=None, is_blur=is_blur,
                                                     is_inline=is_inline)
    await notification.send()


async def main():
    dp.message.middleware(InnerCallbackQueryUniqueClientMiddleware())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
