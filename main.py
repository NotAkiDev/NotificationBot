from aiogram import Bot, Dispatcher
from aiogram import types, F
from aiogram.filters.command import Command
import asyncio
from config_reader import config
from TgUser import TgUser
from StateMachine import StateMachine, State
from dbServing import UsersTable

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()
stm = StateMachine()

# Dictionary to store users
users = {}


async def load_users_from_db():
    global users
    users = {}
    query = UsersTable.select()
    for user in query:
        users[user.uid] = TgUser(
            id=user.uid,
            name=user.name,
            surname=user.surname,
            username=user.username,
            confirm_code=user.confirm_code,
            is_attached=user.is_attached
        )
        # Set user's state
        user_state = State(user.state) if user.state in State.__members__ else State.START
        stm.set_state(user_state)


@dp.message(Command("start"))
async def handler_start(message: types.Message):
    if stm.return_state() == State.START:
        kb = [
            [types.KeyboardButton(text="Connect Account")],
            [types.KeyboardButton(text="Deactivate Account")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Choose action")
        await message.answer("Welcome! What would you like to do?", reply_markup=keyboard)


@dp.message(F.text == "Connect Account")
async def handler_button_activate(message: types.Message):
    if stm.return_state() == State.START:
        stm.set_state(State.ACTIVATE_PROCESS_OPEN)
        user = users.get(message.from_user.id)
        if not user:
            user = TgUser(
                id=message.from_user.id,
                name=message.from_user.first_name,
                surname=message.from_user.last_name,
                username=message.from_user.username
            )
            users[message.from_user.id] = user
        user.activate()
        stm.set_state(State.SEND_CODE)
        await message.answer("Enter the activation code:")
    else:
        await message.answer("Account connection is not available at this stage.")


@dp.message(F.text == "Deactivate Account")
async def handler_button_deactivate(message: types.Message):
    if stm.return_state() in [State.WAIT_NOTIFICATION, State.GET_NOTIFICATION_ANSWER]:
        user = users.get(message.from_user.id)
        if user:
            user.deactivate()
            stm.set_state(State.GET_CODE)
            await message.answer("Enter the deactivation code:")
        else:
            await message.answer("You are not registered.")
    else:
        await message.answer("Account deactivation is not available at this stage.")


@dp.message(lambda message: len(message.text) == 8)
async def code_handler(message: types.Message):
    user = users.get(message.from_user.id)
    if user:
        if stm.return_state() == State.ON_VALIDATION:
            if user.is_valid_code(message.text):
                user.confirm_activate(message.text)
                stm.set_state(State.WAIT_NOTIFICATION)
                await message.answer("Activation code accepted. Account activated.")
            else:
                await message.answer("Invalid activation code.")
        elif stm.return_state() == State.GET_CODE:
            if user.is_valid_code(message.text):
                user.confirm_deactivate()
                stm.set_state(State.DEACTIVATE_PROCESS_CLOSE)
                await message.answer("Deactivation code accepted. Account deactivated.")
            else:
                await message.answer("Invalid deactivation code.")
    else:
        await message.answer("You are not registered.")


async def main():
    await load_users_from_db()  # Load users from database into memory
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
