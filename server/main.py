import asyncio
from aiohttp import web
from .server import ServerLogic

CREDS_PATH = '../creds/creds.json'
CHAT_PATH = '../chat/chats_info.json'


async def main():
    server = ServerLogic(CREDS_PATH, CHAT_PATH)
    app = server.init_server()
    web.run_app(app, host='0.0.0.0', port=3000)


if __name__ == '__main__':
    asyncio.run(main())
