import asyncio
from main import send_notification_to_users
from NotificationState import NotificationState
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class UserNotification:
    def __init__(self, name, text, level, type_, is_blur=None, is_inline=None):
        self.name = name
        self.text = text
        self.level = level
        self.type = type_
        self.is_blur = is_blur
        self.is_inline = is_inline
        self.state = NotificationState.NEW

    async def __send(self):
        await send_notification_to_users(self.name, self.text, self.level)

    async def send(self):
        # Call __send with appropriate reply_markup
        await self.__send()

    def preparing(self):
        if self.is_blur or self.is_inline:
            self.state = NotificationState.PREPARING_TO_SEND

    def feedback(self):
        # Implementation for feedback
        pass


