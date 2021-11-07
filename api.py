import asyncio
from aiohttp import web
import discord
import sys
import json
from random import randint
from time import mktime,time
from datetime import datetime
import socket

with open("config.json") as configFile:
	config = json.load(configFile)

client = discord.Client()
cache = {}

@client.event
async def on_ready():
	print("Bot has authed")
	game = discord.Game("Scraping NameMC")
	await client.change_presence(status=discord.Status.online, activity=game)
	asyncio.create_task(api())

async def lookup(target):
	data = ""
	while len(str(data)) < 10:
		tag = str(randint(int("1"*20),int("9"*20)))
		channel = await client.get_guild(config["server"]).create_text_channel(target)
		try:
			await channel.send("https://namemc.com/search?q="+target+"&c="+tag)
			while True:
				try:
					target = target.lower()
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
					elif "Invalid" or "Too Short" in raw:
						data["status"] = "invalid"
						data["droptime"] = None
				except IndexError:
					await asyncio.sleep(.05)
		finally:
			asyncio.create_task(channel.delete())
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
		else:
			return web.Response(text="Make sure to include a target!\nYou can pass it in the query string (?target=name), or as a header ({\"target\":\"name\"})")

		check = False
		if target in cache:
			if cache[target]["recheck"] < time():
				check = True
		else:
			check = True

		if check:
			while True:
				data = str(await asyncio.wait_for(lookup(target),4))
				if len(data) > 16:
					cache[target.lower()] = {"data":data,"recheck":time()+60*5}
					return web.json_response(data)
		else:
			return web.json_response(json.dumps(cache[target]["data"],indent=3))

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