import aiohttp
import asyncio
import json
import requests
import http.cookies
from aiohttp.client_exceptions import ClientConnectorError


async def main():
    url = "http://localhost:8001/post1"
    myobj = {"somekey": "somevalue"}
    async with aiohttp.ClientSession(
        json_serialize=json.dumps, timeout=aiohttp.ClientTimeout(60, 10, 30, 10)
    ) as session:
        async with session.post(url, json=myobj, cookies={
          # "age": http.cookies.Morsel(age=100, Domain='localhost')
        }) as r:
            pass
        cookies = {}
        cookies.update(r.cookies)
        # age = cookies['age']
        # print(age.key, age.value)
        # async with session.post(url, json=myobj, cookies=cookies) as r:
        #     pass


asyncio.run(main())
