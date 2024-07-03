from server import ServerLogic
import asyncio


async def main():
    server = ServerLogic()
    async with websockets.serve(server.ws_handler, "", 3000, max_size=None):
        print('Server run on 3000')
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
