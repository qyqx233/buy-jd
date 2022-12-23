import asyncio
import aiohttp
from util.http import get_raw, init_session, close_sessoin


async def main():
    try:
        await init_session()
        resp = await get_raw("https://baidu.com")
        print(len(resp))
    except:
        await close_sessoin()


async def main1():
    session = aiohttp.ClientSession()
    resp = await session.get("https://baidu.com")
    print(len(await resp.text()))
    print(resp.url.__class__)
    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main1())
