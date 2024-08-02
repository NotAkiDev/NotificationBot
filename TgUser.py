import random
import string
import peewee
from dbServing import UsersTable


class TgUser:
    def __init__(self, uid, name, surname, username, confirm_code=None, is_attached=False):
        self.uid = uid
        self.name = name
        self.surname = surname
        self.username = username
        self.confirm_code = confirm_code
        self.is_attached = is_attached

    def activate(self):
        print(f"Activating user with ID: {self.uid}")
        self.__send_activate_code()
        user_query = UsersTable.select().where(UsersTable.uid == self.uid)
        if not user_query.exists():
            UsersTable.create(
                uid=self.uid,
                name=self.name,
                surname=self.surname,
                username=self.username,
                confirm_code=self.confirm_code,
                is_attached=self.is_attached,
            )
        else:
            UsersTable.update(
                {
                    UsersTable.confirm_code: self.confirm_code,
                }
            ).where(UsersTable.uid == self.uid).execute()

    def deactivate(self):
        self.__send_deactivate_code()
        UsersTable.update(
            {
                UsersTable.confirm_code: self.confirm_code,
            }
        ).where(UsersTable.uid == self.uid).execute()

    def __is_valid_code(self, taken_code):
        print("Validating activation code...")
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
            ).where(UsersTable.uid == self.uid).execute()
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
            ).where(UsersTable.uid == self.uid).execute()
            print("Account deactivated successfully")
            return True
        return False

    def __send_activate_code(self):
        possible_chars = string.ascii_lowercase + string.digits
        self.confirm_code = ''.join(random.choice(possible_chars) for _ in range(8))
        print(f"Activation code: {self.confirm_code}")

    def __send_deactivate_code(self):
        possible_chars = string.ascii_lowercase + string.digits
        self.confirm_code = ''.join(random.choice(possible_chars) for _ in range(8))
        print(f"Deactivation code: {self.confirm_code}")
