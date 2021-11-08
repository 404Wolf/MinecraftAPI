"""
test.py is a script to test the main api.
It works by spamming 10 requests at localhost (assumes the api is being run on the same pc),
and then recording how long it takes to receive responses
"""

import aiohttp
import asyncio
import sys
from time import time
from random import sample

count = 10 #how many reqs to send
start = time() #record start time

print()
async def main():
	"""
	Main function, with the code for the tester
	"""

	async def spam(session):
		"function that generates a random 3 char and hits the api with it"
		target = "".join(sample("abcdefghijklmnopqrstuvwxyz"*26,3)) #generate a random 3 char
		async with session.get("http://localhost:5000/lookup?target="+target) as resp:
			print(await resp.json()) #print the api's response


	async with aiohttp.ClientSession() as session:
		"Creates a client session for requests, and then spams the api"
		tasks = [] #async task pool
		for x in range(count): #set up tasks
			tasks.append(asyncio.ensure_future(spam(session)))
		await asyncio.gather(*tasks) #run tasks

#set event policy to windows if user is running windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main()) #run main script

#print results of the test
print()
print("Total time taken:",round(time()-start,4))
print("Average time per req:",round((time()-start)/count,4))
print("Total number of reqs sent:",count)