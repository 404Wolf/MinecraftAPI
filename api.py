import asyncio
from aiohttp import web
import discord
import sys
import json
from random import randint,choice
from time import mktime,time
from datetime import datetime
import socket
import logging

with open("config.json") as configFile:
	config = json.load(configFile)

clients = list(discord.Client() for i in range(len(config['tokens'])))
cache = {}

async def lookup(target):
	global channels
	data = ""
	while len(str(data)) < 10:
		channel = choice(channels)
		async def send():
			await channel.send("https://namemc.com/search?q="+target+"&c="+str(randint(int("1"*20),int("9"*20))))
		attempts = 0
		while True:
			try:
				if (attempts == 0) or ((attempts >= 4) and attempts % 4 == 0):
					try:
						await asyncio.wait_for(send(),4)
					except:
						pass
				target = target
				data = {"target":target}
				async for message in channel.history(limit=1):
					messageFromHist = message
				raw = messageFromHist.embeds[0].description
				data["searches"] = int(raw[raw.find("Searches: "):].replace("Searches: ","").replace(" / month",""))
				if "Availability" in raw:
					droptime = mktime(datetime.strptime(raw[:raw.find("Z,")].replace("Time of Availability: ",""), "%Y-%m-%dT%H:%M:%S").timetuple())
					data["status"] = "dropping"
					data["droptime"] = droptime
				elif "Unavailable" in raw:
					data["status"] = "unavailable"
					data["droptime"] = None
				elif "Available*" in raw:
					data["status"] = "available"
					data["droptime"] = None
				elif "Invalid" or "Too" in raw:
					data["status"] = "invalid"
					data["droptime"] = None
				else:
					raise Exception
				break
			except:
				await asyncio.sleep(.075)
				attempts += 1
	return data

async def api():
	routes = web.RouteTableDef()

	@routes.get('/')
	async def api_ping(request):
		return web.Response(text="API for scraping NameMC data")

	@routes.get("/lookup")
	async def api_lookup(request):
		try:
			target = request.headers["target"]
		except KeyError:
			target = request.query_string.replace("target=","")

		target = target.lower()

		if (target not in cache) or (cache[target]["recheck"] < time()):
			data = await lookup(target)
			cache[target] = {}
			cache[target]["data"] = data
			cache[target]["recheck"] = time()+60*10
			return web.json_response(data)

		return web.json_response(cache[target]["data"])

	async def startServer():
		app = web.Application()
		app.add_routes(routes)
		runner = web.AppRunner(app)
		await runner.setup()
		site = web.TCPSite(runner,port=5000)
		await site.start()
		print("API has booted on "+socket.gethostbyname(socket.gethostname())+":5000")

	asyncio.create_task(startServer())

	while True:
		await asyncio.sleep(9)

async def boot():
	global channels

	for client in clients:
		asyncio.create_task(client.start(config['tokens'][clients.index(client)]))

	async def getChannels():
		channels = []
		for client in clients:
			guild = client.get_guild(config['server'])
			for channel in guild.text_channels:
				channels.append(channel)
		return channels

	while True:
		try:
			channels = await getChannels()
			break
		except AttributeError:
			await asyncio.sleep(.1)

	i = 0
	if len(channels) != (len(clients)**2)*50:
		print(len(channels))
		guild = choice(clients).get_guild(config['server'])
		for channel in guild.text_channels:
			await channel.delete()
		for client in clients:
			guild = client.get_guild(config['server'])
			for _ in range(50):
				await guild.create_text_channel("scraper-"+str(i+1))
				i += 1

	channels = await getChannels()

	for client in clients:
		await client.change_presence(status=discord.Status.online, activity=discord.Game("Scraping NameMC"))

	asyncio.create_task(api())
	logging.basicConfig(level=logging.INFO)

	while True:
		await asyncio.sleep(9)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(boot())