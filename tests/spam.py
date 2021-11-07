import aiohttp
import asyncio
import sys
from time import time
from random import sample

count = 1000

async def main():
	async def spam(session):
		target = "".join(sample("abcdefghijklmnopqrstuvwxyz"*26,3))
		start = time()
		async with session.get("http://localhost:5000/lookup?target="+target,timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
			print(await resp.text())

	start = time()

	async with aiohttp.ClientSession() as session:
		tasks = []
		for x in range(count):
			tasks.append(asyncio.create_task(spam(session)))
			await asyncio.sleep(.4)
		await asyncio.wait(tasks)

	print("Total time taken:",round(time()-start,4))
	print("Avg time per req:",round((time()-start)/count,4))
	print("Total reqs:",count)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())