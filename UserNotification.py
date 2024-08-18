import asyncio
from main import send_notification_to_users
from NotificationState import NotificationState
from aiogram.utils.formatting import Spoiler, Text


class UserNotification:
    def __init__(self, name, text, level, type_, is_blur=None, is_inline=None):
        self.name = name
        self.text = text
        self.level = level
        self.type = type_
        self.is_blur = is_blur
        if self.is_blur:
            self.text = "||" + self.text + "||"
        self.is_inline = is_inline
        self.state = NotificationState.NEW

    async def __send(self):
        await send_notification_to_users(self.name, self.text, self.level, self.is_inline)

    async def send(self):
        # Call __send with appropriate reply_markup
        await self.__send()
