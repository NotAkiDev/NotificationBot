from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import asyncio
from typing import Callable, Dict, Any, Awaitable
from aiogram import Router, BaseMiddleware
from config_reader import config
from TgUser import TgUser
from StateMachine import State
from dbServing import UsersTable, NotificationTable
from FeedbackState import FeedbackState
import UserNotification
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, TelegramObject, message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()
users = {}


class InnerCallbackQueryUniqueClientMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]) -> Any:

        user_data = UsersTable.get_or_none(UsersTable.tg_id == event.from_user.id)
        if user_data:
            tg_user = TgUser(
                tg_id=user_data.tg_id,
                name=user_data.name,
                surname=user_data.surname,
                username=user_data.username,
                confirm_code=user_data.confirm_code,
                is_attached=user_data.is_attached
            )
            data["tg_user"] = tg_user
        return await handler(event, data)


dp.message.middleware(InnerCallbackQueryUniqueClientMiddleware())


async def load_users_from_db():
    global users
    query = UsersTable.select()
    users = {}
    for user in query:
        users[int(user.tg_id)] = [TgUser(
            tg_id=user.tg_id,
            name=user.name,
            surname=user.surname,
            username=user.username,
            confirm_code=user.confirm_code,
            is_attached=user.is_attached
        ), State.WAIT_NOTIFICATION if user.is_attached else State.START]
    return users


@dp.message(StateFilter(None), Command("start"))
async def handler_start(message: types.Message, state: FSMContext):
    global users
    if message.from_user.id not in users:
        users[message.from_user.id] = [None, State.START]

    if users[message.from_user.id][1] == State.START:
        kb = [
            [types.KeyboardButton(text="Connect Account")],
            [types.KeyboardButton(text="Deactivate Account")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Choose action")
        await message.answer("Welcome! What would you like to do?", reply_markup=keyboard)
        await state.set_state(State.START)


@dp.message(StateFilter(State.START), F.text == "Connect Account")
async def handler_button_activate(message: types.Message, state: FSMContext, data: Dict[str, Any]):
    global users
    tg_user = data.get("tg_user")
    print(tg_user)
    user_id = message.from_user.id
    if user_id in users:
        users[user_id][0] = TgUser(
            user_id,
            message.from_user.first_name,
            message.from_user.last_name,
            message.from_user.username
        )
        users[user_id][0].activate()
        users[user_id][1] = State.ON_VALIDATION
        await message.answer("Enter the activation code:")
        await state.set_state(State.ON_VALIDATION)
    else:
        await message.answer("You are not registered.")


@dp.message(StateFilter(State.WAIT_NOTIFICATION), F.text == "Deactivate Account")
async def handler_button_deactivate(message: types.Message, state: FSMContext):
    user = users.get(message.from_user.id)
    if user:
        users[message.from_user.id][0].deactivate()
        users[message.from_user.id][1] = State.GET_CODE
        await message.answer("Enter the deactivation code:")
        await state.set_state(State.GET_CODE)
    else:
        await message.answer("You are not registered.")


@dp.message(StateFilter(State.ON_VALIDATION, State.GET_CODE), lambda message: len(message.text) == 8)
async def code_handler(message: types.Message, state: FSMContext):
    global users
    user = users.get(message.from_user.id)
    if user:
        current_state = await state.get_state()
        if current_state == State.ON_VALIDATION:
            if users[message.from_user.id][0].confirm_activate(message.text):
                users[message.from_user.id][1] = State.WAIT_NOTIFICATION
                await message.answer("Activation code accepted. Account activated.")
                await state.set_state(State.WAIT_NOTIFICATION)
            else:
                await message.answer("Invalid activation code.")
                await state.set_state(State.START)
        elif current_state == State.GET_CODE:
            if users[message.from_user.id][0].confirm_deactivate(message.text):
                users[message.from_user.id][1] = State.DEACTIVATE_PROCESS_CLOSE
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


async def send_notification_to_users(name, notification_text, level):
    global users
    users = await load_users_from_db()
    for user_id, (user, state) in users.items():
        if state == State.WAIT_NOTIFICATION:
            notification = NotificationTable.create(
                uid=user_id,
                note_name=name,
                level=level
            )
            if level == "critical":
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="I've read", callback_data=f"read_{notification.id}"))
                await bot.send_message(user_id, notification_text, reply_markup=builder.as_markup())
            else:
                await bot.send_message(user_id, notification_text)


@dp.message(Command("gen"))
async def generate_notification(message: types.Message):
    notification_levels = ["info", "warning", "critical"]
    name = f"Notification_{random.randint(1, 1000)}"
    text = f"This is a {random.choice(['test', 'sample', 'example'])} notification with ID {random.randint(10000, 99999)}."
    level = random.choice(notification_levels)
    notification = UserNotification.UserNotification(name, text, level, type_=None)
    await notification.send()


async def main():
    await load_users_from_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
