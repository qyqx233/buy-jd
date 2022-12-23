import aiohttp
import json
import orjson
import urllib.parse
from typing import Any, Mapping

session: aiohttp.ClientSession = None # type: ignore 


async def init_session():
    global session
    con = aiohttp.TCPConnector(verify_ssl=False)
    session = aiohttp.ClientSession(
        json_serialize=json.dumps, timeout=aiohttp.ClientTimeout(60, 10, 30, 10)
    )


def get_session() -> aiohttp.ClientSession:
    global session
    return session


class SessionContext:
    async def __aenter__(self, *args):
        await init_session()

    async def __aexit__(self, *args):
        await close_sessoin()


async def close_sessoin():
    global session
    if session:
        await session.close()


async def post_json_raw(url, data: Any, headers: Mapping = None) -> Any:
    global session
    async with session.post(url, json=data, headers=headers) as resp:
        response = await resp.read()
        return response


async def post_json(
    url,
    data: Any,
) -> Any:
    global session
    async with session.post(url, json=data) as resp:
        response = await resp.read()
        return orjson.loads(response)


async def post_raw(
    url,
    data: Any,
) -> Any:
    global session
    async with session.post(url, data=data) as resp:
        response = await resp.text()
        return orjson.loads(response)


async def get_raw(url, params: Mapping = None, headers=None, cookies=None):
    global session
    if params is None:
        params = {}
    async with session.get(
        f"{url}?{urllib.parse.urlencode(params)}",
        headers=headers,
        verify_ssl=False,
        cookies=cookies,
    ) as resp:
        return await resp.read()


async def get_queries_json(url, queries: Mapping, headers=None) -> Any:
    global session
    # print([f"{k}={urllib.parse.urlencode(v)}" for k, v in queries.items()])
    # raw = "&".join(f"{k}={urllib.parse.urlencode(v)}"
    #                for k, v in queries.items())
    async with session.get(
        f"{url}?{urllib.parse.urlencode(queries)}", headers=headers
    ) as resp:
        response = await resp.text()
        return orjson.loads(response)


if __name__ == "__main__":
    pass
