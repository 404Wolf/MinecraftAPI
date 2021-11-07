import aiohttp
import asyncio
import sys
from time import time
from random import sample

async def main():
	async def spam(session):
		target = "".join(sample("abcdefghijklmnopqrstuvwxyz"*26,3))
		start = time()
		async with session.get("http://45.63.18.200:5000/lookup?target="+target) as resp:
			print(await resp.json())
			print("Time taken:",time()-start)

	async with aiohttp.ClientSession() as session:
		tasks = []
		for x in range(50):
			tasks.append(asyncio.ensure_future(spam(session)))
		await asyncio.gather(*tasks)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())