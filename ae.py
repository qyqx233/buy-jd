import asyncio
from util.http import get_session, SessionContext


async def main():
    async with SessionContext():
        res = await get_session().get("https://baidu.com", proxy='http://192.168.50.105:1080')
        print(res)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
