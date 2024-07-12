import asyncio
from aiohttp import web
from main_server_manager.server.server_logic import ServerLogic

CREDS_PATH = 'creds/creds.json'
CHAT_PATH = 'chat/chats_info.json'


async def main():
    server = ServerLogic(CREDS_PATH, CHAT_PATH)
    app = server.init_server()
    return app


if __name__ == '__main__':
    app = asyncio.run(main())
    web.run_app(app, host='0.0.0.0', port=3000)
