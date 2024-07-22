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
    uid = CharField(unique=True)  # Ensure UID is unique
    name = CharField()  # User's first name
    surname = CharField(null=True)  # User's surname (optional)
    username = CharField(null=True)  # User's username (optional)
    confirm_code = CharField(null=True)  # Allow null for confirmation code (it can be empty)
    is_attached = BooleanField(default=False)  # Default to False
    state = CharField(default="START")  # Default state

    class Meta:
        database = db  # Define the database to use for this model


# Connect to the database and create the UsersTable if it doesn't exist
def initialize_db():  # For test
    db.connect()
    db.create_tables([UsersTable], safe=True)  # Create tables if they don't exist
