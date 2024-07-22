from enum import Enum

class State(Enum):
    START = "START"
    ACTIVATE_PROCESS_OPEN = "ACTIVATE_PROCESS_OPEN"
    SEND_CODE = "SEND_CODE"
    ON_VALIDATION = "ON_VALIDATION"
    ACTIVATE_PROCESS_CLOSE = "ACTIVATE_PROCESS_CLOSE"
    WAIT_NOTIFICATION = "WAIT_NOTIFICATION"
    GET_NOTIFICATION_ANSWER = "GET_NOTIFICATION_ANSWER"
    DEACTIVATE_PROCESS_OPEN = "DEACTIVATE_PROCESS_OPEN"
    GET_CODE = "GET_CODE"
    DEACTIVATE_PROCESS_CLOSE = "DEACTIVATE_PROCESS_CLOSE"

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
