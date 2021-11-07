import asyncio
from aiohttp import web
import discord
import sys
import json
from random import randint,choice
from time import mktime,time,sleep
from datetime import datetime
import socket

with open("config.json") as configFile:
	config = json.load(configFile)

client = discord.Client()
cache = {}
current = 0
ratelimit = 0

@client.event
async def on_ready():
	global channels
	print("Bot has authed")
	game = discord.Game("Scraping NameMC")
	await client.change_presence(status=discord.Status.online, activity=game)
	asyncio.create_task(api())
	asyncio.create_task(ratelimitReset())
	channels = []
	guild = client.get_guild(config['server'])
	for channel in guild.text_channels:
		channels.append(channel)
	if len(channels) != 100:
		for channel in channels:
			await channel.delete()
		for i in range(100):
			channels.append(await client.get_guild(config["server"]).create_text_channel("scraper-"+str(i+1)))

async def ratelimitReset():
	global ratelimit
	while True:
		ratelimit = 0
		await asyncio.sleep(5)

async def lookup(target):
	global channels
	global current
	data = ""
	while len(str(data)) < 10:
		try:
			channel = channels[current]
		except IndexError:
			current = 0
		finally:
			current += 1
		async def send():
			await channel.send("https://namemc.com/search?q="+target+"&c="+str(randint(int("1"*20),int("9"*20))))
		attempts = 0
		while True:
			try:
				if (attempts == 0) or ((attempts >= 4) and attempts % 4 == 0):
					await send()
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
		global ratelimit

		try:
			target = request.headers["target"]
		except KeyError:
			target = request.query_string.replace("target=","")
		else:
			return web.Response(text="Make sure to include a target!\nYou can pass it in the query string (?target=name), or as a header ({\"target\":\"name\"})")

		target = target.lower()

		if (target not in cache) or (cache[target]["recheck"] < time()):
			try:
				if ratelimit > 20:
					return web.json_response({"target":target,"error":"Ratelimit hit! Please try again in 20-30 seconds."})
				data = await asyncio.wait_for(lookup(target),3)
				cache[target] = {}
				cache[target]["data"] = data
				cache[target]["recheck"] = time()+60*10
				ratelimit += 1
				return web.json_response(data)
			except:
				return web.Response(text="Make sure to include a target!\nYou can pass it in the query string (?target=name), or as a header ({\"target\":\"name\"})")

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
		await asyncio.sleep(0.01)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

client.run(config['token'])