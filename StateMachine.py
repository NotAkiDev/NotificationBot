from enum import Enum
from aiogram.fsm.state import StatesGroup, State
class State(StatesGroup):
    START = State()
    ACTIVATE_PROCESS_OPEN = State()
    SEND_CODE = State()
    ON_VALIDATION = State()
    ACTIVATE_PROCESS_CLOSE = State()
    WAIT_NOTIFICATION = State()
    GET_NOTIFICATION_ANSWER = State()
    DEACTIVATE_PROCESS_OPEN = State()
    GET_CODE = State()
    DEACTIVATE_PROCESS_CLOSE = State()

class StateMachine:
    def __init__(self):
        self.states = list(State)
        self.now = State.START

    def return_state(self):
        return self.now

    def set_state(self, new_state):
        if new_state in State:
            self.now = new_state
            print(f"State updated to: {self.now.value}")
        else:
            print("Attempted to set an invalid state")
