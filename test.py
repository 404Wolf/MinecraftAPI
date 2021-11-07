import aiohttp
import asyncio
import sys
from time import time
from random import sample
import json

start = time()
output = {}
combinations = []
error = 0
for letter1 in tuple("abcdefghijklmnopqrstuvwxyz"):
	for letter2 in tuple("abcdefghijklmnopqrstuvwxyz"):
		for letter3 in tuple("abcdefghijklmnopqrstuvwxyz"):
			combinations.append(letter1+letter2+letter3)
combinations = tuple(set(combinations))

print()
async def main():
	async def spam(target,session):
		global error
		try:
			async with session.get("http://localhost:5000/lookup?target="+target,timeout=aiohttp.ClientTimeout(1)) as resp:
				respJson = await resp.json()
				print(respJson)
				return (target,respJson)
		except:
			error += 1
			print("Errors are now at",error)

	async with aiohttp.ClientSession() as session:
		tasks = []
		for combination in combinations:
			tasks.append(await spam(combination,session))
			await asyncio.sleep(.5)

	for task in tasks:
		output[task[0]] = task[1]

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
print()
print("Total time taken:",round(time()-start,4))
print("Errors",error)

with open("output.json","w") as outputFile:
	json.dump(output,outputFile,indent=3)