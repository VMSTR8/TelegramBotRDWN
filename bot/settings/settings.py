import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMINS = os.environ.get('ADMINS')

WEB_SERVER_HOST = os.environ.get('WEB_SERVER_HOST')
WEB_SERVER_PORT = os.environ.get('WEB_SERVER_PORT')
WEBHOOK_PATH = os.environ.get('WEBHOOK_PATH')
BASE_WEBHOOK_URL = os.environ.get('BASE_WEBHOOK_URL')
