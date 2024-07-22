from enum import Enum


class FeedbackState(Enum):
    CONFIRM = "CONFIRM"
    IN_PROCESS = "IN_PROCESS"
    UNCONFIRM = "UNCONFIRM"
