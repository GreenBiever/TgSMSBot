import aiohttp
import json


async def get_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://jobs.github.com/positions.json") as response:
            data = (await response.content.read()).decode()
            print(data)
            return json.loads(data)
