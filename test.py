import aiohttp
import asyncio
import sys
from time import time
from random import sample

count = 10
start = time()

print()
async def main():
	async def spam(session):
		target = "".join(sample("abcdefghijklmnopqrstuvwxyz"*26,3))
		async with session.get("http://192.168.1.152:5000/lookup?target="+target) as resp:
			print(await resp.json())

	async with aiohttp.ClientSession() as session:
		tasks = []
		for x in range(count):
			tasks.append(asyncio.ensure_future(spam(session)))
		await asyncio.gather(*tasks)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
print()
print("Total time taken:",round(time()-start,4))
print("Average time per req:",round((time()-start)/count,4))
print("Total number of reqs sent:",count)