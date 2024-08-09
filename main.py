from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import asyncio
from config_reader import config
from TgUser import TgUser
from StateMachine import State
from dbServing import UsersTable, NotificationTable
from FeedbackState import FeedbackState
import UserNotification
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

# Dictionary to store users
users = {}


async def load_users_from_db():
    global users
    query = UsersTable.select()
    users = {}
    for user in query:
        users[int(user.uid)] = [TgUser(
            uid=user.uid,
            name=user.name,
            surname=user.surname,
            username=user.username,
            confirm_code=user.confirm_code,
            is_attached=user.is_attached
        ), State.WAIT_NOTIFICATION if user.is_attached else State.START]
        print(f"{user.uid} : {State.WAIT_NOTIFICATION if user.is_attached else State.START}")
    print(users)
    return users


@dp.message(Command("start"))
async def handler_start(message: types.Message):
    global users
    if message.from_user.id not in users.keys():
        users[message.from_user.id] = [None, State.START]

    if users[message.from_user.id][1] == State.START:
        kb = [
            [types.KeyboardButton(text="Connect Account")],
            [types.KeyboardButton(text="Deactivate Account")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Choose action")
        await message.answer("Welcome! What would you like to do?", reply_markup=keyboard)


@dp.message(F.text == "Connect Account")
async def handler_button_activate(message: types.Message):
    global users
    if users[message.from_user.id][1] == State.START:
        users[message.from_user.id][0] = TgUser(message.from_user.id, message.from_user.first_name,
                                                message.from_user.last_name,
                                                message.from_user.username)
        users[message.from_user.id][1] = State.ACTIVATE_PROCESS_OPEN
        users[message.from_user.id][0].activate()
        users[message.from_user.id][1] = State.SEND_CODE
        await message.answer("Enter the activation code:")
        users[message.from_user.id][1] = State.ON_VALIDATION
    else:
        await message.answer("Account connection is not available at this stage.")


@dp.message(F.text == "Deactivate Account")
async def handler_button_deactivate(message: types.Message):
    if users[message.from_user.id][1] in [State.WAIT_NOTIFICATION, State.GET_NOTIFICATION_ANSWER]:
        user = users.get(message.from_user.id)
        if user:
            users[message.from_user.id][0].deactivate()
            users[message.from_user.id][1] = State.GET_CODE
            await message.answer("Enter the deactivation code:")
        else:
            await message.answer("You are not registered.")
    else:
        await message.answer("Account deactivation is not available at this stage.")


@dp.message(lambda message: len(message.text) == 8)
async def code_handler(message: types.Message):
    global users
    user = users.get(message.from_user.id)
    if user:
        if users[message.from_user.id][1] == State.ON_VALIDATION:
            if users[message.from_user.id][0].confirm_activate(message.text):
                users[message.from_user.id][1] = State.WAIT_NOTIFICATION
                await message.answer("Activation code accepted. Account activated.")
            else:
                users[message.from_user.id][1] = State.START
                await message.answer("Invalid activation code.")

        elif users[message.from_user.id][1] == State.GET_CODE:
            if users[message.from_user.id][0].confirm_deactivate(message.text):
                users[message.from_user.id][1] = State.DEACTIVATE_PROCESS_CLOSE
                await message.answer("Deactivation code accepted. Account deactivated.")
                users[message.from_user.id][1] = State.START
            else:
                users[message.from_user.id][1] = State.WAIT_NOTIFICATION
                await message.answer("Invalid deactivation code.")
    else:
        await message.answer("You are not registered.")


@dp.callback_query(lambda callback_query: callback_query.data.startswith("read_"))
async def handle_read_button(callback_query: types.CallbackQuery):
    # Извлекаем ID уведомления из callback_data
    notification_id = int(callback_query.data.split("_")[1])

    # Обновляем состояние в базе данных только для конкретного уведомления
    NotificationTable.update(
        {
            NotificationTable.feedback: FeedbackState.CONFIRM
        }
    ).where(NotificationTable.id == notification_id).execute()

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "You have acknowledged the notification.")


async def send_notification_to_users(name, notification_text, level):
    global users
    users = await load_users_from_db()  # Используем await для получения результата
    for user_id, (user, state) in users.items():
        if state == State.WAIT_NOTIFICATION:
            notification = NotificationTable.create(
                uid=user_id,
                note_name=name,
                level=level
            )
            if level == "critical":
                builder = InlineKeyboardBuilder()
                builder.add((InlineKeyboardButton(text="I've read", callback_data=f"read_{notification.id}")))
                await bot.send_message(user_id, notification_text, reply_markup=builder.as_markup())
            else:
                await bot.send_message(user_id, notification_text)


@dp.message(Command("gen"))
async def mew(message: types.Message):
    notification_levels = ["info", "warning", "critical"]
    name = f"Notification_{random.randint(1, 1000)}"
    text = f"This is a {random.choice(['test', 'sample', 'example'])} notification with ID {random.randint(10000, 99999)}."
    level = random.choice(notification_levels)
    notification = UserNotification.UserNotification(name, text, level, type_=None)
    print("here")
    await notification.send()


async def main():
    await load_users_from_db()  # Load users from database into memory
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
