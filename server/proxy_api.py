class WorkWithAPI:
    def __init__(self):
        super().__init__()
        self.url = api_proxy_url
        self.message_about_funds = False

    async def get_proxies(self, prox_type):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url + f'/proxy/list/{prox_type}') as response:
                if response.ok:
                    result = await response.json()
                    return result['data']['items']
                else:
                    if response.status == 429:
                        await asyncio.sleep(10)
                        return await self.get_proxies(prox_type)

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
            'countryId': 3282888,
            'periodId': '7d',
            'quantity': qty,
            'targetSectionId': 223,
            'targetId': 3281106
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

    async def set_comment_all(self, comment, prox_type):
        all_proxies = await self.get_proxies(prox_type)
        data = {'ids': [], 'comment': comment}

        for proxy in all_proxies:
            if proxy['comment'] != 'ban':
                data['ids'].append(proxy['id'])

        async with aiohttp.ClientSession() as session:
            await session.post(self.url + '/proxy/comment/set', data=json.dumps(data),
                               headers={'Content-Type': 'application/json'})

    async def proxy_processing(self, qty, prox_type):
        all_proxies = await self.get_proxies(prox_type)

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
                    return await self.proxy_processing(qty, prox_type)
        else:
            await self.set_comment(valid_proxies, 'In use')
            return valid_proxies

    async def second_request(self, qty, retries=10):
        all_proxies = await self.get_proxies(prox_type)
        valid_proxies = self.proxy_comment_check(all_proxies, qty)

        if valid_proxies:
            await self.set_comment(valid_proxies, 'In use')
            return valid_proxies
        elif retries != 0:
            retries -= 1
            return await self.second_request(qty, retries)
        else:
            return