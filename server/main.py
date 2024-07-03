import asyncio
from aiohttp import web
from server import ServerLogic


async def main():
    server = ServerLogic()
    app = server.init_server()
    web.run_app(app, host='0.0.0.0', port=3000)


if __name__ == '__main__':
    asyncio.run(main())
