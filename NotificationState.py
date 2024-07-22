from enum import Enum


class NotificationState(Enum):
    NEW = "NEW"
    PREPARING_TO_SEND = "PREPARING_TO_SEND"
    SENDED = "SENDED"
    CONFIRMED = "CONFIRMED"
