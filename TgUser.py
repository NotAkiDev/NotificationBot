import random
import string
import peewee
from dbServing import UsersTable

class TgUser:
    def __init__(self, id, name, surname, username, confirm_code=None, is_attached=False):
        self.id = id
        self.name = name
        self.surname = surname
        self.username = username
        self.confirm_code = confirm_code
        self.is_attached = is_attached

    def activate(self):
        print(f"Activating user with ID: {self.id}")
        self.__send_activate_code()
        user_query = UsersTable.select().where(UsersTable.uid == self.id)
        if not user_query.exists():
            UsersTable.create(
                uid=self.id,
                name=self.name,
                surname=self.surname,
                username=self.username,
                confirm_code=self.confirm_code,
                is_attached=self.is_attached,
                state="ACTIVATE_PROCESS_OPEN"
            )
        else:
            UsersTable.update(
                {
                    UsersTable.confirm_code: self.confirm_code,
                    UsersTable.state: "ACTIVATE_PROCESS_OPEN"  # Update state
                }
            ).where(UsersTable.uid == self.id).execute()

    def deactivate(self):
        print(f"Deactivating user with ID: {self.id}")
        self.__get_deactivate_code()
        UsersTable.update(
            {
                UsersTable.state: "DEACTIVATE_PROCESS_OPEN"
            }
        ).where(UsersTable.uid == self.id).execute()

    def is_valid_code(self, taken_code):
        print("Validating activation code...")
        return taken_code == self.confirm_code

    def confirm_activate(self, user_code):
        if self.is_valid_code(user_code):
            self.is_attached = True
            self.confirm_code = None
            UsersTable.update(
                {
                    UsersTable.is_attached: self.is_attached,
                    UsersTable.confirm_code: None,
                    UsersTable.state: "WAIT_NOTIFICATION"  # Set state after activation
                }
            ).where(UsersTable.uid == self.id).execute()
            print("Account activated successfully")

    def confirm_deactivate(self):
        self.is_attached = False
        self.confirm_code = None
        UsersTable.update(
            {
                UsersTable.is_attached: self.is_attached,
                UsersTable.confirm_code: None,
                UsersTable.state: "DEACTIVATE_PROCESS_CLOSE"
            }
        ).where(UsersTable.uid == self.id).execute()
        print("Account deactivated successfully")

    def __send_activate_code(self):
        possible_chars = string.ascii_lowercase + string.digits
        self.confirm_code = ''.join(random.choice(possible_chars) for _ in range(8))
        print(f"Activation code: {self.confirm_code}")

    def __get_deactivate_code(self):
        possible_chars = string.ascii_lowercase + string.digits
        self.confirm_code = ''.join(random.choice(possible_chars) for _ in range(8))
        print(f"Deactivation code: {self.confirm_code}")
