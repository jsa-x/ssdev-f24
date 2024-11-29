import os

# MySQL credentials
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'Your_User')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Your_Password')
MYSQL_DB = os.getenv('MYSQL_DB', 'keyboard_store')

# Secret key for session management
SECRET_KEY = os.getenv('SECRET_KEY', 'Your_Secret_Key')
