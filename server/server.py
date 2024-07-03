import base64
import os
from aiohttp import web
from aiogram.types import FSInputFile
from server import bot, create_text_pattern, WorkWithAPI, read_json


class ServerLogic:
    def __init__(self, creds_path: str, chat_path: str):
        self.chat_ids = read_json(chat_path)
        self.api = WorkWithAPI(creds_path)
        self.chat_id_flipping = self.chat_ids.get('chat_id_for_flipping_reports')
        self.chat_id_err_backend = self.chat_ids.get('chat_id_for_errors_backend')
        self.chat_id_err_attention = self.chat_ids.get('chat_id_for_errors_attention')
        self.chat_id_report = self.chat_ids.get('chat_id_for_reports')

    def init_server(self):
        app = web.Application()
        app.router.add_get('/get_proxies', self.get_proxies)
        app.router.add_post('/message', self.send_message)
        return app

    def _chat_type_check(self, chat_type):
        if chat_type == 'backend':
            return self.chat_id_err_backend
        elif chat_type == 'attention':
            return self.chat_id_err_attention
        elif chat_type == 'flipping':
            return self.chat_id_flipping
        elif chat_type == 'report':
            return self.chat_id_report

    async def send_message(self, request: web.Request):
        data = await request.json()
        text = data.get('text')
        chat_type = data.get('chat_type')
        chat_id = self._chat_type_check(chat_type)
        await bot.send_message(chat_id, text)
        return web.json_response({'status': 'ok'})

    async def get_proxies(self, request: web.Request):
        proxy_type = request.rel_url.query.get('type', 'isp')
        proxies = await self.api.get_proxies(proxy_type)
        return web.json_response(proxies)

    async def error_attention(self, request):
        shop_name = request["shop_name"]
        message_text = request["message_text"]

        text = f"{shop_name}: {message_text}"

        await bot.send_message(self.chat_id_err_attention, text)

    async def saving_and_sending_file(self, request):
        data = await request.json()
        chat_type = data.get('chat_type')
        caption = data.get('caption')
        file_name = data.get('file_name')
        encoded_file = data.get('file')
        chat_id = self._chat_type_check(chat_type)

        file_data = base64.b64decode(encoded_file)

        with open(f'./{file_name}', 'wb') as file:
            file.write(file_data)

        input_file = FSInputFile(f'./{file_name}')
        await bot.send_document(chat_id, input_file, caption=caption)
        os.remove(f'./{file_name}')

    async def send_report(self, request):
        pass

    async def error_backend(self, request: web.Request):
        data = await request.json()
        error = data.get('error_text')
        shop = data.get('shop_name')

        error_message = f'На "{shop}" ошибка: {error}'
        await bot.send_message(self.chat_id_err_backend, error_message)
