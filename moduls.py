import asyncio
import aiohttp
from aiogram import Bot
from aiogram.types import FSInputFile
import websockets
from settings import (api_proxy_url, bot_token, chat_id_for_errors_attention, chat_id_for_flipping_reports,
                      chat_id_for_reports, brake_down_for_proxy, chat_id_for_errors_backend)
import json
import base64
import os

bot = Bot(bot_token)


def create_text_pattern(shop_name, all_processed, new_nones, new_in_stock, new_price,
                        new_shipping_price, average_processing_time_for_link, time_for_code_processing,
                        bad_info_perc, errors, error_status=False):

    for key, error in errors.items():
        if error:
            error_status = True
            break

    text_pattern = f"""
Закончен чек на магазине "{shop_name}"
Было всего обработано - {all_processed}.
В No Stock - {new_nones}.
В Stock - {new_in_stock}.
Обновилась цена у - {new_price}.
Обновилась доставка у - {new_shipping_price}.

Общее время обработки магазина - {round((time_for_code_processing / 60) / 60, 2)} часов.
Среднее время обработки одной ссылки - {round(average_processing_time_for_link, 2)} секунды.
{f'''
Ошибки:
proxy error - {errors['proxy_errors']}
unknown error - {errors['unknown_errors']}
no block with info - {errors['no_block_with_info']}
no title in link - {errors['no_title_in_link']}
timeout error - {errors['time_out_errors']}
ebay close connection - {errors['ebay_close_connection']}
server close connection - {errors['server_close_connection']}
''' if error_status else ''}
Товары на Амазон обновлены успешно!
{f"Слишком много ошибок прокси - {bad_info_perc * 100}%" if bad_info_perc >= 0.05 else ""}
"""

    return text_pattern


class WorkWithAPI:
    def __init__(self):
        super().__init__()
        self.url = api_proxy_url
        self.message_about_funds = False

    async def get_proxies(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url + '/proxy/list/ipv4') as response:
                if response.ok:
                    result = await response.json()
                    return result['data']['items']
                else:
                    if response.status == 429:
                        await asyncio.sleep(10)
                        return await self.get_proxies()

    @staticmethod
    def proxy_comment_check(all_proxies, qty):
        valid_proxy = []
        for proxy in all_proxies:
            if not proxy['comment'] and len(valid_proxy) < qty:
                valid_proxy.append(proxy)

        if len(valid_proxy) >= qty:
            return valid_proxy
        else:
            return len(valid_proxy)

    async def buy_proxy(self, need_qty, valid_proxy_length):
        qty = need_qty - valid_proxy_length
        data = {
            'countryId': 565,
            'periodId': '1w',
            'quantity': qty,
            'targetSectionId': 79,
            'targetId': 1461
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url + '/order/make', data=json.dumps(data),
                                        headers={'Content-Type': 'application/json'}) as response:

                    return await response.json()
        except Exception as e:
            error = f'Произошла ошибка при попытке купить прокси: {e}'
            await bot.send_message(chat_id_for_errors_backend, error)

    async def look_balance(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url + '/balance/get') as response:
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

    async def set_comment(self, proxy_list, comment):
        data = {'ids': [], 'comment': comment}

        for proxy in proxy_list:
            data['ids'].append(proxy['id'])

        async with aiohttp.ClientSession() as session:
            await session.post(self.url + '/proxy/comment/set', data=json.dumps(data),
                               headers={'Content-Type': 'application/json'})

    async def set_comment_all(self, comment):
        all_proxies = await self.get_proxies()
        data = {'ids': [], 'comment': comment}

        for proxy in all_proxies:
            if proxy['comment'] != 'ban':
                data['ids'].append(proxy['id'])

        async with aiohttp.ClientSession() as session:
            await session.post(self.url + '/proxy/comment/set', data=json.dumps(data),
                               headers={'Content-Type': 'application/json'})

    async def proxy_processing(self, qty):
        all_proxies = await self.get_proxies()

        if len(all_proxies) >= brake_down_for_proxy:
            error = (f'Кол-во купленных прокси равно {len(all_proxies)}. '
                     f'Это превышает установленное ограничение. '
                     f'Пожалуйста, убедитесь что бот покупает прокси исправно и при необходимости увеличьте лимит.')
            await bot.send_message(chat_id_for_errors_backend, error)

        valid_proxies = self.proxy_comment_check(all_proxies, qty)

        if isinstance(valid_proxies, int):
            if self.message_about_funds is False:
                buy_resp = await self.buy_proxy(qty, valid_proxies)

                if buy_resp['errors']:
                    if ['Insufficient funds' in error['message'] for error in buy_resp['errors']]:
                        if self.message_about_funds is False:
                            message = f'На балансе поставщика прокси не достаточно средств для проведения оплаты.'
                            await bot.send_message(chat_id_for_reports, message)
                            self.message_about_funds = True

                        return 'Insufficient funds on proxy service'
                else:
                    if self.message_about_funds is True:
                        self.message_about_funds = False

                if buy_resp['data']['balance'] <= 50:
                    message = f"Баланс на сервисе прокси: {buy_resp['data']['balance']}$."
                    await bot.send_message(chat_id_for_reports, message)
                await asyncio.sleep(3)
                return await self.second_request(qty)
            else:
                balance_res = await self.look_balance()
                if balance_res['data']['summ'] < 1.57:
                    return 'Insufficient funds on proxy service'
                else:
                    self.message_about_funds = False
                    return await self.proxy_processing(qty)
        else:
            await self.set_comment(valid_proxies, 'In use')
            return valid_proxies

    async def second_request(self, qty, retries=10,):
        all_proxies = await self.get_proxies()
        valid_proxies = self.proxy_comment_check(all_proxies, qty)

        if valid_proxies:
            await self.set_comment(valid_proxies, 'In use')
            return valid_proxies
        elif retries != 0:
            retries -= 1
            return await self.second_request(qty, retries)
        else:
            return


class ServerLogic:
    def __init__(self):
        self.api_worker = WorkWithAPI()
        self.semaphore_1 = asyncio.Semaphore(1)
        self.semaphore_5 = asyncio.Semaphore(5)

    async def ws_handler(self, websocket):
        while True:
            try:
                message = json.loads(await websocket.recv())
                response = await self.process_message(message)
                await websocket.send(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            except websockets.exceptions.ConnectionClosedOK:
                print('Connection closed.')
                break

    async def process_message(self, message):
        response = {
            'status': '',
            'message': '',
            'errors': [],
            'data': {}
        }

        try:
            if message['message_type'] == 'get_proxy':
                async with self.semaphore_1:
                    proxies = await self.get_proxy(message)
                response['data']['proxies'] = proxies
            elif message['message_type'] == 'send_report_text':
                async with self.semaphore_5:
                    await self.message_report_send_text(message)
                response['status'], response['message'] = 'success', 'Report was send'
            elif message['message_type'] == 'send_custom_error':
                async with self.semaphore_5:
                    await self.message_send_errors_custom(message)
                response['status'], response['message'] = 'success', 'Custom error was send'
            elif message['message_type'] == 'send_file_processed':
                async with self.semaphore_1:
                    await self.saving_and_sending_file(message, chat_id_for_errors_attention)
                response['status'], response['message'] = 'success', 'File was send'
            elif message['message_type'] == 'send_file_report_flipper':
                async with self.semaphore_1:
                    await self.saving_and_sending_file(message, chat_id_for_flipping_reports)
                response['status'], response['message'] = 'success', 'File was send'
            elif message['message_type'] == 'error':
                async with self.semaphore_5:
                    await self.message_error_send_text(message)
                response['status'], response['message'] = 'success', 'Error was send to Telegram'
            elif message['message_type'] == 'reset_all_proxy':
                async with self.semaphore_1:
                    await self.reset_all_proxies()
                response['status'], response['message'] = 'success', 'All proxies was reset'
            elif message['message_type'] == 'reset_proxy':
                async with self.semaphore_1:
                    await self.reset_proxy(message)
                response['status'], response['message'] = 'success', 'Proxies was reset'
            elif message['message_type'] == 'bad_proxy':
                async with self.semaphore_1:
                    await self.proxy_ban(message)
                response['status'], response['message'] = 'success', 'Proxy was banned'
            else:
                response['status'], response['message'] = 'error', 'Unknown message type'

        except Exception as e:
            response['status'], response['message'] = 'error', str(e)
            response['errors'].append(str(e))

        return response

    async def get_proxy(self, request):
        quantity = request["qty"]
        proxies = await self.api_worker.proxy_processing(quantity)

        return proxies

    async def reset_proxy(self, request):
        await self.api_worker.set_comment(request['proxies'], '')

    async def reset_all_proxies(self):
        await self.api_worker.set_comment_all('')

    async def proxy_ban(self, request):
        await self.api_worker.set_comment(request['proxies'], comment='ban')

    @staticmethod
    async def message_send_errors_custom(request):
        shop_name = request["shop_name"]
        message_text = request["message_text"]

        text = f"{shop_name}: {message_text}"

        await bot.send_message(chat_id_for_errors_attention, text)

    @staticmethod
    async def saving_and_sending_file(request, chat_id):
        caption = request.get('caption')
        file_name = request.get('file_name')
        encoded_file = request.get('file')

        file_data = base64.b64decode(encoded_file)

        with open(f'./{file_name}', 'wb') as file:
            file.write(file_data)

        input_file = FSInputFile(f'./{file_name}')
        await bot.send_document(chat_id, input_file, caption=caption)
        os.remove(f'./{file_name}')

    async def message_report_send_text(self, request):
        shop_name = request.get("shop_name")
        all_processed = request.get("all_processed")
        new_nones = request.get("nones_new")
        new_in_stock = request.get("stock_new")
        new_price = request.get("new_price")
        new_shipping_price = request.get("new_shipping")
        bad_info_perc = request.get("bad_info_perc")
        errors = request.get('errors')
        average_time_for_processing_link = request.get("average_time_for_processing_link")
        time_for_code_processing = request.get("time_of_code_processing")
        proxies = request.get('proxies')

        await self.api_worker.set_comment(proxies, '')

        text = create_text_pattern(shop_name=shop_name, all_processed=all_processed,
                                   new_nones=new_nones, new_in_stock=new_in_stock,
                                   new_price=new_price, new_shipping_price=new_shipping_price,
                                   bad_info_perc=bad_info_perc, time_for_code_processing=time_for_code_processing,
                                   average_processing_time_for_link=average_time_for_processing_link, errors=errors)

        await bot.send_message(chat_id_for_reports, text)

    @staticmethod
    async def message_error_send_text(request):
        error = request['error_text']
        shop = request['shop_name']

        error_message = f'На "{shop}" ошибка: {error}'
        await bot.send_message(chat_id_for_errors_backend, error_message)
