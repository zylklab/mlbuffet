import os

from dotenv import load_dotenv

config_file = '/home/.env'
load_dotenv(config_file)

FLASK_PORT = int(os.getenv('FLASK_PORT'))
CERTFILE = os.getenv('CERTFILE')
KEYFILE = os.getenv('KEYFILE')

