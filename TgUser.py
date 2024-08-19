import random
import string
from dbServing import UsersTable


class TgUser:
    def __init__(self, tg_id, name, surname, username, confirm_code=None, is_attached=False):
        self.tg_id = tg_id
        self.name = name
        self.surname = surname
        self.username = username
        self.confirm_code = confirm_code
        self.is_attached = is_attached

    # For the activation process. Writing user information to the database and adding the activation code
    def activate(self):
        print(f"Activating user with ID: {self.tg_id}")
        self.__send_activate_code()
        UsersTable.update({UsersTable.confirm_code: self.confirm_code}).where(
            UsersTable.tg_id == self.tg_id).execute()

    # For the deactivation process. Writing the activation code
    def deactivate(self):
        self.__send_deactivate_code()
        UsersTable.update({UsersTable.confirm_code: self.confirm_code}).where(UsersTable.tg_id == self.tg_id).execute()

    # There should be a status return to the api here.
    def __is_valid_code(self, taken_code):
        print("Validating")
        # api return
        return taken_code == self.confirm_code

    def confirm_activate(self, user_code):
        if self.__is_valid_code(user_code):
            self.is_attached = True
            self.confirm_code = None
            UsersTable.update(
                {
                    UsersTable.is_attached: self.is_attached,
                    UsersTable.confirm_code: None,
                }
            ).where(UsersTable.tg_id == self.tg_id).execute()
            print("Account activated successfully")
            return True
        return False

    def confirm_deactivate(self, user_code):
        if self.__is_valid_code(user_code):
            self.is_attached = False
            self.confirm_code = None
            UsersTable.update(
                {
                    UsersTable.is_attached: self.is_attached,
                    UsersTable.confirm_code: None,
                }
            ).where(UsersTable.tg_id == self.tg_id).execute()
            print("Account deactivated successfully")
            return True
        return False

    def return_attached(self):
        return self.is_attached

    def __send_activate_code(self):
        possible_chars = string.ascii_lowercase + string.digits
        self.confirm_code = ''.join(random.choice(possible_chars) for _ in range(8))
        print(f"Activation code: {self.confirm_code}")

    def __send_deactivate_code(self):
        possible_chars = string.ascii_lowercase + string.digits
        self.confirm_code = ''.join(random.choice(possible_chars) for _ in range(8))
        print(f"Deactivation code: {self.confirm_code}")
