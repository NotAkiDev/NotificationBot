from peewee import *
from config_reader import config

# Database configuration
db = PostgresqlDatabase(
    config.db_name.get_secret_value(),
    user=config.user.get_secret_value(),
    password=config.passw.get_secret_value(),
    host=config.host.get_secret_value(),
    port=config.port.get_secret_value()
)


class UsersTable(Model):
    id = CharField()
    uid = CharField(unique=True)  # Ensure UID is unique
    name = CharField()  # User's first name
    surname = CharField(null=True)  # User's surname (optional)
    username = CharField(null=True)  # User's username (optional)
    confirm_code = CharField(null=True)  # Allow null for confirmation code (it can be empty)
    is_attached = BooleanField(default=False)  # Default to False

    class Meta:
        database = db  # Define the database to use for this model


# Connect to the database and create the UsersTable if it doesn't exist

class NotificationTable(Model):
    uid = CharField()
    note_name = CharField()
    level = CharField()
    feedback = CharField(null=True)

    class Meta:
        database = db


def initialize_db():
    db.connect()
    db.create_tables([UsersTable, NotificaionTable], safe=True)  # Create tables if they don't exist

initialize_db()