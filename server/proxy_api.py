import aiohttp
import asyncio
import json
from .telegram_bot import bot
from .utils import read_json


class WorkWithAPI:
    def __init__(self, creds_path: str):
        self.creds = read_json(creds_path)
        api_key = self.creds.get('api_proxy_token')
        api_domain = self.creds.get('api_proxy_url')
        self.api_url = api_domain + api_key
        chat: dict = read_json('../chat/chats_info.json')
        self.chat_id_for_flipping_reports = chat.get('chat_id_for_flipping_reports')
        self.chat_id_for_errors_backend = chat.get('chat_id_for_errors_backend')
        self.chat_id_for_errors_attention = chat.get('chat_id_for_errors_attention')
        self.chat_id_for_reports = chat.get('chat_id_for_reports')

    async def get_proxies(self, prox_type):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url + f'/proxy/list/{prox_type}') as response:
                if response.ok:
                    result = await response.json()
                    return result['data']['items']
                else:
                    if response.status == 429:
                        await asyncio.sleep(10)
                        return await self.get_proxies(prox_type)

    async def buy_proxy(self, need_qty, valid_proxy_length):
        qty = need_qty - valid_proxy_length
        data = {
            'countryId': 3282888,
            'periodId': '7d',
            'quantity': qty,
            'targetSectionId': 223,
            'targetId': 3281106
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url + '/order/make', data=json.dumps(data),
                                        headers={'Content-Type': 'application/json'}) as response:

                    return await response.json()
        except Exception as e:
            error = f'Произошла ошибка при попытке купить прокси: {e}'
            await bot.send_message(self.chat_id_for_errors_backend, error)

    async def look_balance(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url + '/balance/get') as response:
                if response.ok:
                    return await response.json()
                else:
                    return {
                        'status': 'error',
                        'data': {
                            'summ': 0
                        },
                        'errors': []
                    }
