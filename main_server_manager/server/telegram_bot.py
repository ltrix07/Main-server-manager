from aiogram import Bot
from main_server_manager.server.utils import read_json


token_path = './creds/creds.json'
creds = read_json(token_path)
bot = Bot(creds.get('bot_token'))
