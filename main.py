from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.filters.command import Command
import asyncio
from config_reader import config

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()


@dp.message(Command("start"))
async def handler_start(message: types.Message):
    await message.answer("Heeeelo")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
