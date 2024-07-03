import base64
import os
from aiohttp import web
from aiogram.types import FSInputFile
from server import bot, create_text_pattern, WorkWithAPI


class ServerLogic:
    def __init__(self, creds_path: str):
        self.api = WorkWithAPI(creds_path)

    def init_server(self):
        app = web.Application()
        app.router.add_get('/get_proxies', self.get_proxies)
        return app

    async def get_proxies(self, request: web.Request):
        proxy_type = request.rel_url.query.get('type', 'isp')
        proxies = await self.api.get_proxies(proxy_type)
        return web.json_response(proxies)

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
                    proxies = await self.get_proxy(message, 'isp')
                response['data']['proxies'] = proxies
            if message['message_type'] == 'get_proxy_all_isp':
                async with self.semaphore_1:
                    proxies = await self.api_worker.get_proxies('isp')
                if len(proxies) < 100:
                    message = f'Кол-во прокси у поставщика {len(proxies)}. @L_trix'
                    await bot.send_message(chat_id_for_errors_backend, message)
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
                    await self.reset_all_proxies('isp')
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

    async def get_proxy(self, request, prox_type):
        quantity = request["qty"]
        proxies = await self.api_worker.proxy_processing(quantity, prox_type)

        return proxies

    async def reset_proxy(self, request):
        await self.api_worker.set_comment(request['proxies'], '')

    async def reset_all_proxies(self, prox_type):
        await self.api_worker.set_comment_all('', prox_type)

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
        add_to_amz = request.get('amz_updated')

        await self.api_worker.set_comment(proxies, '')

        text = create_text_pattern(shop_name=shop_name, all_processed=all_processed,
                                   new_nones=new_nones, new_in_stock=new_in_stock,
                                   new_price=new_price, new_shipping_price=new_shipping_price,
                                   bad_info_perc=bad_info_perc, time_for_code_processing=time_for_code_processing,
                                   average_processing_time_for_link=average_time_for_processing_link, errors=errors,
                                   amz_updated_status=add_to_amz)

        await bot.send_message(chat_id_for_reports, text)

    @staticmethod
    async def message_error_send_text(request):
        error = request['error_text']
        shop = request['shop_name']

        error_message = f'На "{shop}" ошибка: {error}'
        await bot.send_message(chat_id_for_errors_backend, error_message)
